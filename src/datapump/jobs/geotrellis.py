from typing import Dict, Any, List, Optional
from itertools import groupby
from pathlib import Path
from pprint import pformat
from enum import Enum
import urllib
import csv
import io

from ..globals import GLOBALS, LOGGER
from ..clients.aws import get_emr_client, get_s3_client, get_s3_path_parts
from ..commands import Analysis, AnalysisInputTable
from ..jobs.jobs import (
    AnalysisResultTable,
    Job,
    JobStatus,
)

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

    @staticmethod
    def get_feature_fields(feature_type):
        if feature_type == GeotrellisFeatureType.wdpa:
            return [
                "wdpa_protected_area__id",
                "wdpa_protected_area__name",
                "wdpa_protected_area__iucn_cat",
                "wdpa_protected_area__iso",
                "wdpa_protected_area__status",
            ]
        elif feature_type == GeotrellisFeatureType.gadm:
            return ["iso", "adm1", "adm2"]
        elif feature_type == GeotrellisFeatureType.geostore:
            return ["geostore__id"]
        elif feature_type == GeotrellisFeatureType.feature:
            return ["feature__id"]


class GeotrellisJob(Job):
    table: AnalysisInputTable
    status: JobStatus
    analysis_version: str
    features_1x1: str
    sync_version: str = None
    feature_type: GeotrellisFeatureType = GeotrellisFeatureType.feature
    geotrellis_version: str
    sync: bool = False
    change_only: bool = False
    emr_job_id: str = None
    result_tables: List[AnalysisResultTable] = []

    def start_analysis(self):
        name = f"{self.table.dataset}_{self.table.analysis}_{self.analysis_version}__{self.id}"
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

    def update_status(self) -> None:
        cluster_description = get_emr_client().describe_cluster(
            ClusterId=self.emr_job_id
        )
        status = cluster_description["Cluster"]["Status"]

        LOGGER.info(
            f"EMR job {self.emr_job_id} has state {status['State']} for reason {pformat(status['StateChangeReason'])}"
        )
        if (
            status["State"] == "TERMINATED"
            and status["StateChangeReason"]["Code"] == "ALL_STEPS_COMPLETED"
        ):
            self.status = JobStatus.analyzed
            self.result_tables = self._get_result_tables()
        elif (
            GLOBALS.env == "test"
            and status["State"] == "WAITING"
            and status["StateChangeReason"]["Code"] == "USER_REQUEST"
        ):
            self.status = JobStatus.analyzed
            self.result_tables = self._get_result_tables()
        elif status["State"] == "TERMINATED_WITH_ERRORS":
            self.status = JobStatus.failed
        elif (
            status["State"] == "TERMINATED"
            and status["StateChangeReason"]["Code"] == "USER_REQUEST"
        ):
            # this can happen if someone manually terminates the EMR job, which means the step function should stop
            # since we can't know if it completed correctly
            self.status = JobStatus.failed
        else:
            self.status = JobStatus.analyzing

    def _get_feature_type(self) -> GeotrellisFeatureType:
        if self.table.dataset == "wdpa_protected_areas":
            return GeotrellisFeatureType.wdpa
        elif self.table.dataset == "global_administrative_areas":
            return GeotrellisFeatureType.gadm
        elif "geostore" in self.table.dataset:
            return GeotrellisFeatureType.geostore
        else:
            return GeotrellisFeatureType.feature

    def _get_result_tables(self) -> List[AnalysisResultTable]:
        result_path = self._get_result_path(include_analysis=True)
        bucket, prefix = get_s3_path_parts(result_path)

        LOGGER.debug(f"Looking for analysis results at {result_path}")
        resp = get_s3_client().list_objects_v2(Bucket=bucket, Prefix=prefix)

        keys = [
            item["Key"] for item in resp["Contents"] if item["Key"].endswith(".csv")
        ]

        result_tables = [
            self._get_result_table(bucket, path, list(files))
            for path, files in groupby(keys, lambda key: Path(key).parent)
        ]

        return result_tables

    def _get_result_table(
        self, bucket: str, path: Path, files: List[str]
    ) -> AnalysisResultTable:
        analysis_agg, feature_agg = (path.parts[-1], path.parts[-2])

        result_dataset = f"{self.table.dataset}__{self.table.analysis}"
        if self.feature_type == "gadm":
            result_dataset += f"__{feature_agg}_{analysis_agg}"
        else:
            result_dataset += f"__{analysis_agg}"

        sources = [f"s3://{bucket}/{file}" for file in files]
        return AnalysisResultTable(
            dataset=result_dataset,
            version=self.analysis_version,
            source_uri=sources,
            index_columns=self._get_index_cols(analysis_agg, feature_agg),
            table_schema=self._get_table_schema(sources[0]),
        )

    def _get_index_cols(
        self, analysis_agg: str, feature_agg: Optional[str] = None
    ) -> List[str]:
        id_col_constructor = {
            ("gadm", "iso"): ["iso"],
            ("gadm", "adm1"): ["iso", "adm1"],
            ("gadm", "adm2"): ["iso", "adm1", "adm2"],
            ("wdpa", None): ["wdpa_protected_area__id"],
            ("geostore", None): ["geostore__id"],
        }

        try:
            cols = id_col_constructor[(self.feature_type, feature_agg)]
        except KeyError:
            cols = ["feature_id"]

        analysis_col_constructor = {
            (Analysis.tcl, "change"): [
                "umd_tree_cover_density_2000__threshold",
                "umd_tree_cover_loss__year",
            ],
            (Analysis.tcl, "summary"): ["umd_tree_cover_density_2000__threshold"],
            (Analysis.glad, "daily_alerts"): ["is__confirmed_alert", "alert__date"],
            (Analysis.glad, "weekly_alerts"): [
                "is__confirmed_alert",
                "alert__year",
                "alert__week",
            ],
            (Analysis.viirs, "daily_alerts"): ["confidence__cat", "alert__date"],
            (Analysis.viirs, "weekly_alerts"): [
                "confidence__cat",
                "alert__year",
                "alert__week",
            ],
            (Analysis.modis, "daily_alerts"): ["confidence__cat", "alert__date"],
            (Analysis.modis, "weekly_alerts"): [
                "confidence__cat",
                "alert__year",
                "alert__week",
            ],
        }

        try:
            cols += analysis_col_constructor[(self.table.analysis, analysis_agg)]
        except KeyError:
            pass

        return cols

    def _get_table_schema(self, source_uri: str) -> List[Dict[str, Any]]:
        bucket, key = get_s3_path_parts(source_uri)
        s3_host = (
            GLOBALS.aws_endpoint_uri
            if GLOBALS.aws_endpoint_uri
            else "https://s3.amazonaws.com"
        )
        http_uri = f"{s3_host}/{bucket}/{key}"

        LOGGER.info(f"Checking column names at source {http_uri}")
        src_url_open = urllib.request.urlopen(http_uri)  # type: ignore
        src_csv = csv.reader(
            io.TextIOWrapper(src_url_open, encoding="utf-8"), delimiter="\t"
        )
        header_row = next(src_csv)

        table_schema = []
        for field_name in header_row:
            is_whitelist = "whitelist" in source_uri
            field_type = self._get_field_type(field_name, is_whitelist)

            table_schema.append({"field_name": field_name, "field_type": field_type})

        return table_schema

    def _get_field_type(self, field, is_whitelist=False):
        if is_whitelist:
            # if whitelist, everything but ID fields should be bool
            if field in GeotrellisFeatureType.get_feature_fields(self.feature_type):
                return "text"
            else:
                return "boolean"
        else:
            if (
                field.endswith("__Mg")
                or field.endswith("__ha")
                or field.endswith("__K")
                or field.endswith("__MW")
                or field == "latitude"
                or field == "longitude"
            ):
                return "double precision"
            elif (
                field.endswith("__threshold")
                or field.endswith("__count")
                or field.endswith("__perc")
                or field.endswith("__year")
                or field.endswith("__week")
                or field == "adm1"
                or field == "adm2"
            ):
                return "integer"
            elif field.startswith("is__"):
                return "boolean"
            else:
                return "text"

    def _calculate_worker_count(self) -> int:
        """
        Calculate a heuristic for number of workers appropriate for job based on the size
        of the input features.

        Uses global constant WORKER_COUNT_PER_GB_FEATURES to determine number of worker per GB of features.
        Uses global constant WORKER_COUNT_MIN to determine minimum number of workers.

        Multiplies by weights for specific analyses.

        :param job: input job
        :return: calculate number of works appropriate for job size
        """
        bucket, key = get_s3_path_parts(self.features_1x1)
        resp = get_s3_client().head_object(Bucket=bucket, Key=key)
        byte_size = resp["ContentLength"]

        analysis_weight = 1.0
        if self.table.analysis == Analysis.tcl:
            analysis_weight *= 1.25

        if self.change_only:
            analysis_weight *= 0.75

        worker_count = round(
            (byte_size / 1000000000)
            * GLOBALS.worker_count_per_gb_features
            * analysis_weight
        )
        return max(worker_count, GLOBALS.worker_count_min)

    def _get_step(self) -> Dict[str, Any]:
        step_args = [
            "spark-submit",
            "--deploy-mode",
            "cluster",
            "--class",
            "org.globalforestwatch.summarystats.SummaryMain",
            f"{GLOBALS.geotrellis_jar_path}/treecoverloss-assembly-{self.geotrellis_version}.jar",
            "--output",
            self._get_result_path(),
            "--features",
            self.features_1x1,
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
            "HadoopJarStep": {"Jar": GLOBALS.command_runner_jar, "Args": step_args},
        }

    def _get_result_path(self, include_analysis=False) -> str:
        result_path = f"s3://{GLOBALS.s3_bucket_pipeline}/geotrellis/results/{self.analysis_version}/{self.table.dataset}"
        if include_analysis:
            result_path += f"/{GeotrellisAnalysis[self.table.analysis].value}"

        return result_path

    @staticmethod
    def _run_job_flow(name, instances, steps, applications, configurations):
        client = get_emr_client()

        request = {
            "Name": name,
            "ReleaseLabel": GLOBALS.emr_version,
            "LogUri": f"s3://{GLOBALS.s3_bucket_pipeline}/geotrellis/logs",
            "Steps": steps,
            "Instances": instances,
            "Applications": applications,
            "Configurations": configurations,
            "VisibleToAllUsers": True,
            "BootstrapActions": [
                {
                    "Name": "Install GDAL",
                    "ScriptBootstrapAction": {
                        "Path": f"s3://{GLOBALS.s3_bucket_pipeline}/geotrellis/bootstrap/gdal.sh",
                        "Args": ["3.1.2"],
                    },
                },
            ],
            "Tags": [
                {"Key": "Project", "Value": "Global Forest Watch"},
                {"Key": "Job", "Value": "GeoTrellis Summary Statistics"},
            ],
        }

        if GLOBALS.emr_instance_profile:
            request["JobFlowRole"] = GLOBALS.emr_instance_profile
        if GLOBALS.emr_service_role:
            request["ServiceRole"] = GLOBALS.emr_service_role

        LOGGER.info(f"Sending EMR request:\n{pformat(request)}")

        response = client.run_job_flow(**request)

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

        if GLOBALS.ec2_key_name:
            instances["Ec2KeyName"] = GLOBALS.ec2_key_name

        if GLOBALS.public_subnet_ids:
            instances["Ec2SubnetIds"] = GLOBALS.public_subnet_ids

        return instances

    @staticmethod
    def _applications() -> List[Dict[str, str]]:
        return [
            {"Name": "Spark"},
            {"Name": "Zeppelin"},
            {"Name": "Ganglia"},
        ]

    @staticmethod
    def _configurations(worker_instance_count: int) -> List[Dict[str, Any]]:
        return [
            {
                "Classification": "spark",
                "Properties": {"maximizeResourceAllocation": "true"},
                "Configurations": [],
            },
            {
                "Classification": "spark-defaults",
                "Properties": {
                    "spark.executor.memory": "5G",
                    "spark.driver.memory": "5G",
                    "spark.driver.cores": "1",
                    "spark.driver.maxResultSize": "3G",
                    "spark.yarn.appMasterEnv.LD_LIBRARY_PATH": "/usr/local/miniconda/lib/:/usr/local/lib",
                    "spark.rdd.compress": "true",
                    "spark.executor.cores": "1",
                    "spark.executorEnv.LD_LIBRARY_PATH": "/usr/local/miniconda/lib/:/usr/local/lib",
                    "spark.sql.shuffle.partitions": str(
                        (70 * worker_instance_count) - 1
                    ),
                    "spark.executor.defaultJavaOptions": "-XX:+UseParallelGC -XX:+UseParallelOldGC -XX:OnOutOfMemoryError='kill -9 %p'",
                    "spark.shuffle.spill.compress": "true",
                    "spark.shuffle.compress": "true",
                    "spark.default.parallelism": str((70 * worker_instance_count) - 1),
                    "spark.executor.memoryOverhead": "2G",
                    "spark.shuffle.service.enabled": "true",
                    "spark.driver.defaultJavaOptions": "-XX:+UseParallelGC -XX:+UseParallelOldGC -XX:OnOutOfMemoryError='kill -9 %p'",
                    "spark.executor.instances": str((7 * worker_instance_count) - 1),
                    "spark.dynamicAllocation.enabled": "false",
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


class FireAlertsGeotrellisJob(GeotrellisJob):
    alert_type: str
    alert_source: List[str]
