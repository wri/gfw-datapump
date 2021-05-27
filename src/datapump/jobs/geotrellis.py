import csv
import io
import urllib
from datetime import date
from enum import Enum
from itertools import groupby
from pathlib import Path
from pprint import pformat
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel

from ..clients.aws import get_emr_client, get_s3_client, get_s3_path_parts
from ..clients.data_api import DataApiClient
from ..commands.analysis import Analysis, AnalysisInputTable
from ..commands.sync import SyncType
from ..globals import GLOBALS, LOGGER
from ..jobs.jobs import (
    AnalysisResultTable,
    Index,
    Job,
    JobStatus,
    JobStep,
    Partition,
    Partitions,
)

WORKER_INSTANCE_TYPES = ["r5.2xlarge", "r4.2xlarge"]  # "r6g.2xlarge"
MASTER_INSTANCE_TYPE = "r5.2xlarge"


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


class GeotrellisJobStep(str, Enum):
    starting = "starting"
    analyzing = "analyzing"
    uploading = "uploading"


class GeotrellisJob(Job):
    table: AnalysisInputTable
    status: JobStatus
    analysis_version: str
    features_1x1: str
    sync_version: Optional[str] = None
    feature_type: GeotrellisFeatureType = GeotrellisFeatureType.feature
    geotrellis_version: str
    sync: bool = False
    sync_type: Optional[SyncType] = None
    change_only: bool = False
    emr_job_id: Optional[str] = None
    version_overrides: Dict[str, Any] = {}
    result_tables: List[AnalysisResultTable] = []

    def next_step(self):
        if self.step == JobStep.starting:
            self.start_analysis()
            self.status = JobStatus.executing
            self.step = GeotrellisJobStep.analyzing
        elif self.step == GeotrellisJobStep.analyzing:
            status = self.check_analysis()
            if status == JobStatus.complete:
                if not self.result_tables:
                    self.result_tables = self._get_result_tables()

                self.upload()
                self.step = GeotrellisJobStep.uploading
            elif status == JobStatus.failed:
                self.status = JobStatus.failed
        elif self.step == GeotrellisJobStep.uploading:
            self.status = self.check_upload()

    def start_analysis(self):
        self.emr_job_id = self._run_job_flow(*self._get_emr_inputs())

    def check_analysis(self) -> JobStatus:
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
            return JobStatus.complete
        elif (
            GLOBALS.env == "test"
            and status["State"] == "WAITING"
            and status["StateChangeReason"]["Code"] == "USER_REQUEST"
        ):
            return JobStatus.complete
        elif status["State"] == "TERMINATED_WITH_ERRORS":
            return JobStatus.failed
        elif (
            status["State"] == "TERMINATED"
            and status["StateChangeReason"]["Code"] == "USER_REQUEST"
        ):
            # this can happen if someone manually terminates the EMR job, which means the step function should stop
            # since we can't know if it completed correctly
            return JobStatus.failed
        else:
            return JobStatus.executing

    def upload(self):
        client = DataApiClient()

        for table in self.result_tables:
            if self.sync_version:
                # temporarily just appending sync versions to analysis version instead of using version inheritance
                if (
                    self.table.analysis == Analysis.glad
                    and self.sync_type != SyncType.rw_areas
                ):
                    client.create_vector_version(
                        table.dataset,
                        table.version,
                        table.source_uri,
                        [index.dict() for index in table.indices]
                        if table.indices
                        else table.indices,
                        table.cluster.dict() if table.cluster else table.cluster,
                        table.table_schema,
                        table.partitions.dict()
                        if table.partitions
                        else table.partitions,
                        table.longitude_field,
                        table.latitude_field,
                    )
                else:
                    if self.sync_type == SyncType.rw_areas:
                        version = client.get_latest_version(table.dataset)
                    else:
                        version = table.version

                    client.append(table.dataset, version, table.source_uri)
            else:
                client.create_dataset_and_version(
                    table.dataset,
                    table.version,
                    table.source_uri,
                    [index.dict() for index in table.indices]
                    if table.indices
                    else table.indices,
                    table.cluster.dict() if table.cluster else table.cluster,
                    table.table_schema,
                    table.partitions.dict() if table.partitions else table.partitions,
                    table.longitude_field,
                    table.latitude_field,
                )

    def check_upload(self) -> JobStatus:
        client = DataApiClient()

        all_saved = True
        for table in self.result_tables:
            if self.sync_type == SyncType.rw_areas:
                version = client.get_latest_version(table.dataset)
            else:
                version = table.version

            status = client.get_version(table.dataset, version)["status"]
            if status == "failed":
                return JobStatus.failed

            all_saved &= status == "saved"

        if all_saved:
            if (
                self.table.analysis == Analysis.glad
                and self.sync_version
                and self.sync_type != SyncType.rw_areas
            ):
                for table in self.result_tables:
                    client.set_latest(table.dataset, self.sync_version)
                    dataset = client.get_dataset(table.dataset)
                    versions = sorted(dataset["versions"])

                    versions_to_delete = versions[: -GLOBALS.max_versions]
                    for version in versions_to_delete:
                        client.delete_version(table.dataset, version)

            return JobStatus.complete

        return JobStatus.executing

    def _get_emr_inputs(self):
        name = f"{self.table.dataset}_{self.table.analysis}_{self.analysis_version}__{self.id}"
        self.feature_type = self._get_feature_type()

        steps = [self._get_step()]

        worker_count = self._calculate_worker_count(self.features_1x1)
        instances = self._instances(worker_count)
        applications = self._applications()
        configurations = self._configurations(worker_count)

        return name, instances, steps, applications, configurations

    def _get_feature_type(self) -> GeotrellisFeatureType:
        if self.table.dataset == "wdpa_protected_areas":
            return GeotrellisFeatureType.wdpa
        elif self.table.dataset == "gadm":
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
            item["Key"]
            for item in resp["Contents"]
            if item["Key"].endswith(".csv") and "download" not in item["Key"]
        ]

        result_tables = [
            self._get_result_table(bucket, path, list(files))
            for path, files in groupby(keys, lambda key: Path(key).parent)
        ]

        return result_tables

    def _get_result_table(
        self, bucket: str, path: Path, files: List[str]
    ) -> AnalysisResultTable:
        feature_agg: Optional[str]
        analysis_agg, feature_agg = (path.parts[-1], path.parts[-2])

        if (
            self.table.dataset == "gadm"
            and self.table.analysis == Analysis.viirs
            and analysis_agg == "all"
        ):
            result_dataset = "nasa_viirs_fire_alerts"
            feature_agg = None
        else:
            result_dataset = f"{self.table.dataset}__{self.table.analysis}"
            if self.feature_type == "gadm":
                result_dataset += f"__{feature_agg}_{analysis_agg}"
            else:
                feature_agg = None
                result_dataset += f"__{analysis_agg}"

        sources = [f"s3://{bucket}/{file}" for file in files]

        if analysis_agg in self.version_overrides:
            version = self.version_overrides[analysis_agg]
        elif (
            self.sync_version
            and self.table.analysis == Analysis.glad
            and "alerts" in analysis_agg
        ):
            version = self.sync_version
        else:
            version = self.analysis_version

        indices, cluster = self._get_indices_and_cluster(analysis_agg, feature_agg)
        partitions = self._get_partitions(analysis_agg, feature_agg)
        table_schema = self._get_table_schema(sources[0])

        result_table = {
            "dataset": result_dataset,
            "version": version,
            "source_uri": sources,
            "indices": indices,
            "cluster": cluster,
            "table_schema": table_schema,
        }

        if partitions:
            result_table["partitions"] = partitions
        if analysis_agg == "all":
            result_table["latitude_field"] = "latitude"
            result_table["longitude_field"] = "longitude"

        return AnalysisResultTable(**result_table)

    def _get_indices_and_cluster(
        self, analysis_agg: str, feature_agg: Optional[str] = None
    ) -> Tuple[List[Index], Index]:
        indices = []

        id_col_constructor: Dict[Tuple[str, Optional[str]], List[str]] = {
            ("gadm", "iso"): ["iso"],
            ("gadm", "adm1"): ["iso", "adm1"],
            ("gadm", "adm2"): ["iso", "adm1", "adm2"],
            ("gadm", None): ["iso", "adm1", "adm2"],
            ("all", None): [],
            ("wdpa", None): ["wdpa_protected_area__id"],
            ("geostore", None): ["geostore__id"],
            ("feature", None): ["feature__id"],
        }

        try:
            if analysis_agg != "all":
                cols = id_col_constructor[(self.feature_type, feature_agg)]
            else:
                # disaggregated points have no ID
                cols = []
        except KeyError as e:
            LOGGER.error(f"Unable to find index for {analysis_agg}/{feature_agg}")
            raise e

        analysis_col_constructor: Dict[Tuple[Analysis, str], List[str]] = {
            (Analysis.tcl, "change"): [
                "umd_tree_cover_density__threshold",
                "umd_tree_cover_loss__year",
            ],
            (Analysis.tcl, "summary"): ["umd_tree_cover_density__threshold"],
            (Analysis.glad, "daily_alerts"): ["is__confirmed_alert", "alert__date"],
            (Analysis.glad, "weekly_alerts"): [
                "is__confirmed_alert",
                "alert__year",
                "alert__week",
            ],
            (Analysis.viirs, "daily_alerts"): ["confidence__cat", "alert__date"],
            (Analysis.viirs, "all"): ["confidence__cat", "alert__date"],
            (Analysis.viirs, "weekly_alerts"): [
                "confidence__cat",
                "alert__year",
                "alert__week",
            ],
            (Analysis.modis, "daily_alerts"): ["confidence__cat", "alert__date"],
            (Analysis.modis, "all"): ["confidence__cat", "alert__date"],
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

        cluster = Index(index_type="btree", column_names=cols)
        indices.append(cluster)

        if analysis_agg == "all":
            cluster = Index(index_type="gist", column_names=["geom_wm"])
            indices += [Index(index_type="gist", column_names=["geom"]), cluster]

        return indices, cluster

    def _get_partitions(
        self, analysis_agg: str, feature_agg: Optional[str] = None
    ) -> Optional[Partitions]:
        if analysis_agg == "all":
            # for all points, partition by month
            partition_schema = []
            for year in range(2012, 2023):
                for month in range(1, 13):
                    start_value = date(year, month, 1).strftime("%Y-%m-%d")
                    end_month = month + 1 if month < 12 else 1
                    end_year = year if month < 12 else year + 1
                    end_value = date(end_year, end_month, 1).strftime("%Y-%m-%d")
                    partition_suffix = f"y{year}_m{month}"
                    partition_schema.append(
                        Partition(
                            partition_suffix=partition_suffix,
                            start_value=start_value,
                            end_value=end_value,
                        )
                    )

            return Partitions(
                partition_type="range",
                partition_column="alert__date",
                partition_schema=partition_schema,
            )

        return None

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
                if field == "adm1" or field == "adm2":
                    return "integer"
                else:
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

    def _calculate_worker_count(self, limiting_src) -> int:
        """
        Calculate a heuristic for number of workers appropriate for job based on the size
        of the input features.

        Uses global constant WORKER_COUNT_PER_GB_FEATURES to determine number of worker per GB of features.
        Uses global constant WORKER_COUNT_MIN to determine minimum number of workers.

        Multiplies by weights for specific analyses.

        :return: calculate number of works appropriate for job size
        """
        # if using a wildcard for a folder, just use hardcoded value
        if "*.tsv" in limiting_src:
            if GLOBALS.env == "production":
                if self.table.analysis == Analysis.tcl:
                    return 200
                else:
                    return 100
            else:
                return 50
        elif self.sync_type == SyncType.rw_areas and self.table.analysis in [
            Analysis.viirs,
            Analysis.modis,
        ]:
            return 15

        bucket, key = get_s3_path_parts(limiting_src)
        resp = get_s3_client().head_object(Bucket=bucket, Key=key)
        byte_size = resp["ContentLength"]

        analysis_weight = 1.0
        if self.table.analysis == Analysis.tcl:
            analysis_weight *= 1.25
        if self.change_only:
            analysis_weight *= 0.75
        # wdpa just has very  complex geometries
        if self.table.dataset == "wdpa_protected_areas":
            analysis_weight *= 0.25

        worker_count = round(
            (byte_size / 1000000000)
            * GLOBALS.worker_count_per_gb_features
            * analysis_weight
        )
        return max(worker_count, GLOBALS.worker_count_min)

    def _get_step(self) -> Dict[str, Any]:
        analysis = GeotrellisAnalysis[self.table.analysis].value
        if "firealerts" in analysis:
            analysis = "firealerts"

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
            self.feature_type.value.split("_")[0],
            "--analysis",
            analysis,
        ]

        # These limit the extent to look at for certain types of analyses
        if self.table.analysis == Analysis.tcl:
            step_args.append("--tcl")
        elif self.table.analysis == Analysis.glad:
            step_args.append("--glad")

        if self.change_only:
            step_args.append("--change_only")

        if (
            GLOBALS.env != "production"
            and self.feature_type == GeotrellisFeatureType.gadm
        ):
            step_args.append("--iso_start")
            step_args.append("BRA")
            step_args.append("--iso_end")
            step_args.append("COK")

        return {
            "Name": self.table.analysis.value,
            "ActionOnFailure": "TERMINATE_CLUSTER",
            "HadoopJarStep": {"Jar": GLOBALS.command_runner_jar, "Args": step_args},
        }

    def _get_result_path(self, include_analysis=False) -> str:
        version = self.sync_version if self.sync_version else self.analysis_version
        result_path = f"s3://{GLOBALS.s3_bucket_pipeline}/geotrellis/results/{version}/{self.table.dataset}"
        if self.sync_type:
            result_path += f"/{self.sync_type.value}"
        if include_analysis:
            result_path += f"/{GeotrellisAnalysis[self.table.analysis].value}"

        return result_path

    def _run_job_flow(self, name, instances, steps, applications, configurations):
        client = get_emr_client()

        tags = [
            {"Key": "Project", "Value": "Global Forest Watch"},
            {"Key": "Job", "Value": "GeoTrellis Summary Statistics"},
            {"Key": "Dataset", "Value": self.table.dataset},
            {"Key": "Analysis", "Value": self.table.analysis},
        ]

        if self.sync_type:
            tags.append({"Key": "Sync Type", "Value": self.sync_type})

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
            "Tags": tags,
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
                    # "spark.executor.memory": "5G",
                    # "spark.driver.memory": "5G",
                    # "spark.driver.cores": "1",
                    "spark.driver.maxResultSize": "3G",
                    "spark.yarn.appMasterEnv.LD_LIBRARY_PATH": "/usr/local/miniconda/lib/:/usr/local/lib",
                    "spark.rdd.compress": "true",
                    # "spark.executor.cores": "1",
                    "spark.executorEnv.LD_LIBRARY_PATH": "/usr/local/miniconda/lib/:/usr/local/lib",
                    # "spark.sql.shuffle.partitions": str(
                    #     (70 * worker_instance_count) - 1
                    # ),
                    "spark.executor.defaultJavaOptions": "-XX:+UseParallelGC -XX:+UseParallelOldGC -XX:OnOutOfMemoryError='kill -9 %p'",
                    "spark.shuffle.spill.compress": "true",
                    "spark.shuffle.compress": "true",
                    # "spark.default.parallelism": str((70 * worker_instance_count) - 1),
                    # "spark.executor.memoryOverhead": "2G",
                    "spark.shuffle.service.enabled": "true",
                    "spark.driver.defaultJavaOptions": "-XX:+UseParallelGC -XX:+UseParallelOldGC -XX:OnOutOfMemoryError='kill -9 %p'",
                    # "spark.executor.instances": str((7 * worker_instance_count) - 1),
                    "spark.dynamicAllocation.enabled": "true",  # "false",
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
    alert_sources: Optional[List[str]] = []

    FIRE_SOURCE_DEFAULT_PATHS: Dict[str, str] = {
        "viirs": f"s3://{GLOBALS.s3_data_lake_pipeline}/nasa_viirs_fire_alerts/v1/vector/epsg-4326/tsv",
        "modis": f"s3://{GLOBALS.s3_data_lake_pipeline}/nasa_modis_fire_alerts/v6/vector/epsg-4326/tsv",
    }

    def _get_step(self):
        step = super()._get_step()
        step_args = step["HadoopJarStep"]["Args"]

        step_args.append("--fire_alert_type")
        step_args.append(self.alert_type)

        if not self.alert_sources:
            self.alert_sources = [
                f"{self.FIRE_SOURCE_DEFAULT_PATHS[self.alert_type]}/scientific/*.tsv",
                f"{self.FIRE_SOURCE_DEFAULT_PATHS[self.alert_type]}/near_real_time/*.tsv",
            ]

        for src in self.alert_sources:
            step_args.append("--fire_alert_source")
            step_args.append(src)

        return step

    def _calculate_worker_count(self, limiting_src: str) -> int:
        if self.sync_version and self.alert_sources and len(self.alert_sources) == 1:
            return super()._calculate_worker_count(self.alert_sources[0])
        else:
            return super()._calculate_worker_count(limiting_src)


class ContinueGeotrellisJobsCommand(BaseModel):
    command: str

    class ContinueGeotrellisJobsParameters(BaseModel):
        jobs: List[Union[FireAlertsGeotrellisJob, GeotrellisJob]]

    parameters: ContinueGeotrellisJobsParameters
