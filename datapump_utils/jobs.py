from uuid import UUID
from enum import Enum
from typing import Dict, Any, List
from itertools import groupby
from pathlib import Path

from pydantic import BaseModel
import boto3

from datapump_utils.analysis import AnalysisInputTable
from datapump_utils.globals import (
    RESULT_BUCKET,
    MASTER_INSTANCE_TYPE,
    WORKER_INSTANCE_TYPES,
    EC2_KEY_NAME,
    PUBLIC_SUBNET_IDS,
    EMR_SERVICE_ROLE,
    EMR_INSTANCE_PROFILE,
    EMR_VERSION,
    GEOTRELLIS_JAR_PATH,
    WORKER_COUNT_MIN,
    WORKER_COUNT_PER_GB_FEATURES,
)
from datapump_utils.aws import get_emr_client, get_s3_client
from datapump_utils.s3 import get_s3_path_parts
from datapump_utils.analysis import Analysis, AnalysisInputTable


class JobType(str, Enum):
    full = "full"


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    complete = "complete"
    failed = "failed"


class GeotrellisChangeAggregates(str, Enum):
    tcl = ["change"]
    glad = ["daily_alerts", "weekly_alerts"]
    viirs = ["daily_alerts", "weekly_alerts"]
    modis = ["daily_alerts", "weekly_alerts"]


class GeotrellisSummaryAggregates(str, Enum):
    tcl = ["summary", "whitelist"]
    glad = ["summary", "whitelist"]
    viirs = ["whitelist"]
    modis = ["whitelist"]


class GadmChangeAggregates(str, Enum):
    tcl = ["change"]
    glad = ["daily_alerts", "weekly_alerts"]
    viirs = ["daily_alerts", "weekly_alerts"]
    modis = ["daily_alerts", "weekly_alerts"]


class Job(BaseModel):
    job_id: UUID
    job_type: JobType


class AnalysisResultTable(BaseModel):
    dataset: str
    version: str
    source_uri: List[str]
    index_columns: List[str]


class GeotrellisJob(Job):
    table: AnalysisInputTable
    version: str
    features_1x1: str
    feature_type: str
    geotrellis_jar_version: str
    change_only: bool = False
    status: JobStatus = JobStatus.pending
    emr_job_id: str = None
    result_tables: List[AnalysisResultTable] = []

    def start_analysis(self):
        name = (
            f"{self.table.dataset}_{self.table.analysis}_{self.version}__{self.job_id}"
        )
        steps = self._get_step()

        worker_count = self._calculate_worker_count()
        instances = self._instances(worker_count)
        applications = self._applications()
        configurations = self._configurations(worker_count)

        self.emr_job_id = self._run_job_flow(
            name, instances, steps, applications, configurations
        )
        self.status = JobStatus.running

    def update_status(self):
        cluster_description = get_emr_client().describe_cluster(
            ClusterId=self.emr_job_id
        )
        status = cluster_description["Cluster"]["Status"]

        if (
            status["State"] == "TERMINATED"
            and status["StateChangeReason"]["Code"] == "ALL_STEPS_COMPLETED"
        ):
            self.status = JobStatus.complete
            self.result_tables = self._get_result_tables()
        elif status["State"] == "TERMINATED_WITH_ERRORS":
            self.status = JobStatus.failed
        else:
            self.status = JobStatus.running

    def _get_result_tables(self):
        bucket, prefix = get_s3_path_parts(self._get_result_path(include_analysis=True))

        resp = get_s3_client().list_objects_v2(Bucket=bucket, Prefix=prefix)

        keys = [item["Key"] for item in resp["Contents"]]

        result_tables = []
        for dir, files in groupby(keys, lambda key: Path(key).parent):
            aggregation = dir.parts[-1]
            result_dataset = (
                f"{self.table.dataset}__{self.table.analysis}__{aggregation}"
            )

            result_tables.append(
                AnalysisResultTable(
                    dataset=result_dataset,
                    version=self.version,
                    source_uri=list(files),
                    index_columns=self._get_index_cols(aggregation),
                )
            )

        return result_tables

    def _get_index_cols(self, aggregation: str):
        cols = ["id"]

        if self.table.analysis == Analysis.tcl:
            cols += [
                "umd_tree_cover_loss__year",
                "umd_tree_cover_density_2000__threshold",
            ]
        if self.table.analysis == Analysis.glad:
            cols += ["confirmation__status"]
            if aggregation == "daily_alerts":
                cols += ["alert__date"]
            elif aggregation == "weekly_alerts":
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
        byte_size = boto3.resource("s3").Bucket(bucket).Object(key).content_length

        analysis_weight = 1.0
        if self.table.analysis == AnalysisInputTable.tcl:
            analysis_weight *= 1.25

        if self.change_only:
            analysis_weight *= 0.75

        worker_count = round(
            (byte_size / 1000000) * WORKER_COUNT_PER_GB_FEATURES * analysis_weight
        )
        return max(worker_count, WORKER_COUNT_MIN)

    def _get_step(self) -> Dict[str, Any]:
        step_args = [
            "spark-submit",
            "--deploy-mode",
            "cluster",
            "--class",
            "org.globalforestwatch.summarystats.SummaryMain",
            f"{GEOTRELLIS_JAR_PATH}/{self.geotrellis_jar_version}",
            "--output",
            self._get_result_path(),
            "--feature_type",
            self.feature_type,
            "--analysis",
            self.table.analysis,
        ]

        # These limit the extent to look at for certain types of analyses
        if self.table.analysis == Analysis.tcl:
            step_args.append("--tcl")
        elif self.table.analysis == Analysis.glad:
            step_args.append("--glad")

        if self.change_only:
            step_args.append("--change_only")

        return {
            "Name": self.table.analysis,
            "ActionOnFailure": "TERMINATE_CLUSTER",
            "HadoopJarStep": {"Jar": "command-runner.jar", "Args": step_args},
        }

    def _get_result_path(self, include_analysis=False):
        result_path = f"s3://{RESULT_BUCKET}/geotrellis/results/{self.version}/{self.table.dataset}"
        if include_analysis:
            result_path += f"/{self.table.analysis}"

        return result_path

    @staticmethod
    def _run_job_flow(name, instances, steps, applications, configurations):
        client = get_emr_client()

        response = client.run_job_flow(
            Name=name,
            ReleaseLabel=EMR_VERSION,
            LogUri=f"s3://{RESULT_BUCKET}/geotrellis/logs",  # TODO should this be param?
            Instances=instances,
            Steps=steps,
            Applications=applications,
            Configurations=configurations,
            VisibleToAllUsers=True,
            JobFlowRole=EMR_INSTANCE_PROFILE,
            ServiceRole=EMR_SERVICE_ROLE,
            Tags=[
                {"Key": "Project", "Value": "Global Forest Watch"},
                {"Key": "Job", "Value": "GeoTrellis Summary Statistics"},
            ],  # flake8 --ignore
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
