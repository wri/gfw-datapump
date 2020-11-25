from typing import Dict, Any, List
from itertools import groupby
from pathlib import Path
from pprint import pformat
from enum import Enum

from datapump.jobs.jobs import JobStatus
from datapump.globals import (
    S3_BUCKET_PIPELINE,
    EC2_KEY_NAME,
    PUBLIC_SUBNET_IDS,
    LOGGER,
    EMR_VERSION,
    GEOTRELLIS_JAR_PATH,
    WORKER_COUNT_MIN,
    WORKER_COUNT_PER_GB_FEATURES,
    ENV
)
from datapump.clients.aws import get_emr_client, get_s3_client
from datapump.util.s3 import get_s3_path_parts
from datapump.jobs.jobs import Analysis, AnalysisInputTable, AnalysisResultTable, Job

WORKER_INSTANCE_TYPES = ["r4.2xlarge", "r5.2xlarge"]
MASTER_INSTANCE_TYPE = "r4.2xlarge"


class GeotrellisAnalysis(str, Enum):
    """
    Supported analyses to run on datasets
    """
    tcl = "annualupdate_minimal"
    glad = "gladalerts"
    viirs = "firealerts_viirs"
    modis = "firealerts_modis"


class GeotrellisFeatureType(str, Enum):
    gadm = "gadm"
    wdpa = "wdpa"
    geostore = "geostore"
    feature = "feature"

class GeotrellisJob(Job):
    table: AnalysisInputTable
    status: JobStatus
    version: str
    features_1x1: str
    feature_type: GeotrellisFeatureType = GeotrellisFeatureType.feature
    geotrellis_jar_version: str
    change_only: bool = False
    emr_job_id: str = None
    result_tables: List[AnalysisResultTable] = []

    def start_analysis(self):
        name = f"{self.table.dataset}_{self.table.analysis}_{self.version}__{self.id}"
        self.feature_type = self._get_feature_type()

        steps = [self._get_step()]

        worker_count = 5  # self._calculate_worker_count()
        instances = self._instances(worker_count)
        applications = self._applications()
        configurations = self._configurations(worker_count)

        self.emr_job_id = self._run_job_flow(
            name, instances, steps, applications, configurations
        )
        self.status = JobStatus.analyzing

    def update_status(self):
        cluster_description = get_emr_client().describe_cluster(
            ClusterId=self.emr_job_id
        )
        status = cluster_description["Cluster"]["Status"]

        LOGGER.info(f"EMR job {self.emr_job_id} has state {status['State']} for reason {status['StateChangeReason']['Code']}")
        if (
            status["State"] == "TERMINATED"
            and status["StateChangeReason"]["Code"] == "ALL_STEPS_COMPLETED"
        ):
            self.status = JobStatus.analyzed
            self.result_tables = self._get_result_tables()
        elif (
            ENV == "test" and
            status["State"] == "WAITING"
            and status["StateChangeReason"]["Code"] == "USER_REQUEST"
        ):
            self.status = JobStatus.analyzed
            self.result_tables = self._get_result_tables()
        elif status["State"] == "TERMINATED_WITH_ERRORS":
            self.status = JobStatus.failed

            self.status = JobStatus.analyzed
        else:
            self.status = JobStatus.analyzing

    def _get_feature_type(self) -> GeotrellisFeatureType:
        if self.table.dataset == "wdpa_protected_areas":
            return GeotrellisFeatureType.wdpa
        elif self.table.dataset == "global_administrative_areas":
            return GeotrellisFeatureType.gadm
        else:
            return GeotrellisFeatureType.feature

    def _get_result_tables(self):
        result_path = self._get_result_path(include_analysis=True)
        bucket, prefix = get_s3_path_parts(result_path)

        LOGGER.debug(f"Looking for analysis results at {result_path}")
        resp = get_s3_client().list_objects_v2(Bucket=bucket, Prefix=prefix)

        keys = [item["Key"] for item in resp["Contents"]]

        result_tables = [
            self._get_result_table(path, files) for path, files in groupby(keys, lambda key: Path(key).parent)
        ]

        return result_tables

    def _get_result_table(self, path: str, files: List[str]):
        analysis_agg, feature_agg = (path.parts[-1], path.parts[-2])

        result_dataset = f"{self.table.dataset}__{self.table.analysis}"
        if self.feature_type == "gadm":
            result_dataset += f"__{feature_agg}_{analysis_agg}"
        else:
            result_dataset += f"__{analysis_agg}"

        return AnalysisResultTable(
                dataset=result_dataset,
                version=self.version,
                source_uri=list(files),
                index_columns=self._get_index_cols(analysis_agg, feature_agg)
            )

    def _get_index_cols(self, analysis_agg: str, feature_agg: str):
        if self.feature_type == "gadm":
            cols = ["iso"]
            if feature_agg == "adm1":
                cols += ["adm1"]
            elif feature_agg == "adm2":
                cols += ["adm1", "adm2"]
        elif self.feature_type == "wdpa":
            cols = ["wdpa_id"]
        elif self.feature_type == "geostore":
            cols = ["geostore_id"]
        else:
            cols = ["feature_id"]

        if self.table.analysis == Analysis.tcl:
            cols += ["umd_tree_cover_density_2000__threshold"]
            if analysis_agg == "change":
                cols += ["umd_tree_cover_loss__year",]
        if self.table.analysis == Analysis.glad:
            cols += ["confirmation__status"]
            if analysis_agg == "daily_alerts":
                cols += ["alert__date"]
            elif analysis_agg == "weekly_alerts":
                cols += ["alert__year", "alert__week"]

        return cols

    def _calculate_worker_count(self):
        """
        Calculate a heuristic for number of workers appropriate for job based on the size
        of the input features.

        Uses global constant WORKER_COUNT_PER_GB_FEATURES to determine number of worker per GB of features.
        Uses global constant WORKER_COUNT_MIN to determine minimum number of workers.

        Multiples by weights for specific analyses.

        :param job: input job
        :return: calculate number of works appropriate for job size
        """
        bucket, key = get_s3_path_parts(self.features_1x1)
        resp = get_s3_client().head_object(Bucket=bucket, Key=key)
        byte_size = resp['ContentLength']

        analysis_weight = 1.0
        if self.table.analysis == Analysis.tcl:
            analysis_weight *= 1.25

        if self.change_only:
            analysis_weight *= 0.75

        worker_count = round(
            (byte_size / 1000000000) * WORKER_COUNT_PER_GB_FEATURES * analysis_weight
        )
        return max(worker_count, WORKER_COUNT_MIN)

    def _get_step(self) -> Dict[str, Any]:
        step_args = [
            "spark-submit",
            "--deploy-mode",
            "cluster",
            "--class",
            "org.globalforestwatch.summarystats.SummaryMain",
            f"{GEOTRELLIS_JAR_PATH}/treecoverloss-assembly-{self.geotrellis_jar_version}.jar",
            "--output",
            self._get_result_path(),
            "--feature_type",
            self.feature_type,
            "--analysis",
            GeotrellisAnalysis[self.table.analysis].value,
        ]

        # These limit the extent to look at for certain types of analyses
        if self.table.analysis == Analysis.tcl:
            step_args.append("--tcl")
        elif self.table.analysis == Analysis.glad:
            step_args.append("--glad")

        if self.change_only:
            step_args.append("--change_only")

        return {
            "Name": self.table.analysis.value,
            "ActionOnFailure": "TERMINATE_CLUSTER",
            "HadoopJarStep": {
                "Jar": f"{GEOTRELLIS_JAR_PATH}/treecoverloss-assembly-{self.geotrellis_jar_version}.jar",
                "Args": step_args
            },
        }

    def _get_result_path(self, include_analysis=False):
        result_path = f"s3://{S3_BUCKET_PIPELINE}/geotrellis/results/{self.version}/{self.table.dataset}"
        if include_analysis:
            result_path += f"/{GeotrellisAnalysis[self.table.analysis].value}"

        return result_path

    @staticmethod
    def _run_job_flow(name, instances, steps, applications, configurations):
        client = get_emr_client()

        request = {
            "Name": name,
            "ReleaseLabel": EMR_VERSION,
            "LogUri": f"s3://{S3_BUCKET_PIPELINE}/geotrellis/logs",
            "Steps": steps,
            "Instances": instances,
            "Applications": applications,
            "Configurations": configurations,
            "VisibleToAllUsers": True,
            "Tags": [
                {"Key": "Project", "Value": "Global Forest Watch"},
                {"Key": "Job", "Value": "GeoTrellis Summary Statistics"},
            ],
        }

        LOGGER.info(f"Sending EMR request:\n{pformat(request)}")

        response = client.run_job_flow(
            **request
            # Name=name,
            # ReleaseLabel=EMR_VERSION,
            # LogUri=f"s3://{S3_BUCKET_PIPELINE}/geotrellis/logs",  # TODO should this be param?
            # Instances=instances,
            # Steps=steps,
            # Applications=applications,
            # Configurations=configurations,
            # VisibleToAllUsers=True,
            # # JobFlowRole=EMR_INSTANCE_PROFILE,
            # # ServiceRole=EMR_SERVICE_ROLE,
            # Tags=[
            #     {"Key": "Project", "Value": "Global Forest Watch"},
            #     {"Key": "Job", "Value": "GeoTrellis Summary Statistics"},
            # ],  # flake8 --ignore
        )

        return response["JobFlowId"]

    @staticmethod
    def _instances(worker_instance_count: int) -> Dict[str, Any]:
        instances = {
            "InstanceFleets": [
                {
                    "Name": "geotrellis-master",
                    "InstanceFleetType": "MASTER",
                    "TargetOnDemandCapacity": 1,
                    "InstanceTypeConfigs": [
                        {
                            "InstanceType": MASTER_INSTANCE_TYPE,
                            "EbsConfiguration": {
                                "EbsBlockDeviceConfigs": [
                                    {
                                        "VolumeSpecification": {
                                            "VolumeType": "gp2",
                                            "SizeInGB": 10,
                                        },
                                        "VolumesPerInstance": 1,
                                    }
                                ],
                                "EbsOptimized": True,
                            },
                        }
                    ],
                },
                {
                    "Name": "geotrellis-cores",
                    "InstanceFleetType": "CORE",
                    "TargetSpotCapacity": worker_instance_count,
                    "InstanceTypeConfigs": [
                        {
                            "InstanceType": instance_type,
                            "EbsConfiguration": {
                                "EbsBlockDeviceConfigs": [
                                    {
                                        "VolumeSpecification": {
                                            "VolumeType": "gp2",
                                            "SizeInGB": 10,
                                        },
                                        "VolumesPerInstance": 1,
                                    }
                                ],
                                "EbsOptimized": True,
                            },
                        }
                        for instance_type in WORKER_INSTANCE_TYPES
                    ],
                },
            ],
            "KeepJobFlowAliveWhenNoSteps": False,
            "TerminationProtected": False,
        }

        if EC2_KEY_NAME:
            instances["Ec2KeyName"] = EC2_KEY_NAME

        if PUBLIC_SUBNET_IDS:
            instances["Ec2SubnetIds"] = PUBLIC_SUBNET_IDS

        return instances

    @staticmethod
    def _applications() -> List[Dict[str, str]]:
        return [
            {"Name": "Spark"},
            {"Name": "Zeppelin"},
            {"Name": "Ganglia"},
        ]

    @staticmethod
    def _configurations(worker_instance_count: str) -> List[Dict[str, Any]]:
        return [
            {
                "Classification": "spark",
                "Properties": {"maximizeResourceAllocation": "true"},
                "Configurations": [],
            },
            {
                "Classification": "spark-defaults",
                "Properties": {
                    "spark.executor.memory": "6G",
                    "spark.driver.memory": "6G",
                    "spark.driver.cores": "1",
                    "spark.driver.maxResultSize": "3G",
                    "spark.rdd.compress": "true",
                    "spark.executor.cores": "1",
                    "spark.sql.shuffle.partitions": str(
                        (70 * worker_instance_count) - 1
                    ),
                    "spark.shuffle.spill.compress": "true",
                    "spark.shuffle.compress": "true",
                    "spark.default.parallelism": str((70 * worker_instance_count) - 1),
                    "spark.shuffle.service.enabled": "true",
                    "spark.executor.extraJavaOptions": "-XX:+UseParallelGC -XX:+UseParallelOldGC -XX:OnOutOfMemoryError='kill -9 %p'",
                    "spark.executor.instances": str((7 * worker_instance_count) - 1),
                    "spark.yarn.executor.memoryOverhead": "1G",
                    "spark.dynamicAllocation.enabled": "false",
                    "spark.driver.extraJavaOptions": "-XX:+UseParallelGC -XX:+UseParallelOldGC -XX:OnOutOfMemoryError='kill -9 %p'",
                },
                "Configurations": [],
            },
            {
                "Classification": "yarn-site",
                "Properties": {
                    "yarn.nodemanager.pmem-check-enabled": "false",
                    "yarn.resourcemanager.am.max-attempts": "1",
                    "yarn.nodemanager.vmem-check-enabled": "false",
                },
                "Configurations": [],
            },
        ]
