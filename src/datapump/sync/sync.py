from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Type
from uuid import uuid1

import dateutil.tz as tz
from datapump.clients.data_api import DataApiClient

from ..clients.aws import get_s3_client, get_s3_path_parts
from ..clients.datapump_store import DatapumpConfig
from ..commands.analysis import FIRES_ANALYSES, AnalysisInputTable
from ..commands.sync import SyncType
from ..commands.version_update import RasterTileCacheParameters, RasterTileSetParameters
from ..globals import GLOBALS, LOGGER
from ..jobs.geotrellis import FireAlertsGeotrellisJob, GeotrellisJob, Job
from ..jobs.jobs import JobStatus
from ..jobs.version_update import RasterVersionUpdateJob
from ..sync.fire_alerts import get_tmp_result_path, process_active_fire_alerts
from ..sync.rw_areas import create_1x1_tsv
from ..util.gpkg_util import update_geopackage
from ..util.slack import slack_webhook


class Sync(ABC):
    @abstractmethod
    def __init__(self, sync_version: str):
        ...

    @abstractmethod
    def build_jobs(self, config: DatapumpConfig) -> List[Job]:
        ...


class FireAlertsSync(Sync):
    def __init__(self, sync_version: str):
        self.sync_version: str = sync_version
        self.fire_alerts_type: Optional[SyncType] = None
        self.fire_alerts_uri: Optional[str] = None

    def build_jobs(self, config: DatapumpConfig) -> List[Job]:
        if self.fire_alerts_type is None:
            raise RuntimeError("No Alert type set")

        return [
            FireAlertsGeotrellisJob(
                id=str(uuid1()),
                status=JobStatus.starting,
                analysis_version=config.analysis_version,
                sync_version=self.sync_version,
                sync_type=config.sync_type,
                table=AnalysisInputTable(
                    dataset=config.dataset,
                    version=config.dataset_version,
                    analysis=config.analysis,
                ),
                features_1x1=config.metadata["features_1x1"],
                geotrellis_version=config.metadata["geotrellis_version"],
                alert_type=self.fire_alerts_type.value,
                alert_sources=[self.fire_alerts_uri],
                change_only=True,
                version_overrides=config.metadata.get("version_overrides", {}),
            )
        ]


class ViirsSync(FireAlertsSync):
    def __init__(self, sync_version: str):
        super(ViirsSync, self).__init__(sync_version)
        self.fire_alerts_type = SyncType.viirs
        self.fire_alerts_uri = process_active_fire_alerts(self.fire_alerts_type.value)

        # try to update geopackage, but still move on if it fails
        try:
            viirs_local_path = get_tmp_result_path("VIIRS")
            update_geopackage(viirs_local_path)
        except Exception as e:
            LOGGER.exception(e)
            slack_webhook(
                "ERROR", "Error updating fires geopackage. Check logs for more details."
            )


class ModisSync(FireAlertsSync):
    def __init__(self, sync_version: str):
        super(ModisSync, self).__init__(sync_version)
        self.fire_alerts_type = SyncType.modis
        self.fire_alerts_uri = process_active_fire_alerts(self.fire_alerts_type.value)


class GladSync(Sync):
    DATASET_NAME = "umd_glad_landsat_alerts"

    def __init__(self, sync_version: str):
        self.sync_version = sync_version
        self.should_sync_glad = self._check_for_new_glad()

    def build_jobs(self, config: DatapumpConfig) -> List[Job]:
        if self.should_sync_glad:
            return [
                GeotrellisJob(
                    id=str(uuid1()),
                    status=JobStatus.starting,
                    analysis_version=config.analysis_version,
                    sync_version=self.sync_version,
                    sync_type=config.sync_type,
                    table=AnalysisInputTable(
                        dataset=config.dataset,
                        version=config.dataset_version,
                        analysis=config.analysis,
                    ),
                    features_1x1=config.metadata["features_1x1"],
                    geotrellis_version=config.metadata["geotrellis_version"],
                    change_only=True,
                    version_overrides=config.metadata.get("version_overrides", {}),
                ),
                RasterVersionUpdateJob(
                    id=str(uuid1()),
                    status=JobStatus.starting,
                    dataset=self.DATASET_NAME,
                    version=self.sync_version,
                    tile_set_parameters=RasterTileSetParameters(
                        source_uri=[
                            f"s3://{GLOBALS.s3_bucket_data_lake}/{self.DATASET_NAME}/raw/tiles.geojson"
                        ],
                        grid="10/100000",
                        data_type="uint16",
                        pixel_meaning="date_conf",
                        compute_stats=False,
                        num_processes=24,
                        timeout_sec=21600,
                    ),
                ),
            ]
        else:
            return []

    def _check_for_new_glad(self):
        bucket, path = get_s3_path_parts(GLOBALS.s3_glad_path)
        response = get_s3_client().get_object(
            Bucket=bucket, Key=f"{path}/events/status"
        )

        last_modified_datetime = response["LastModified"]
        status = response["Body"].read().strip().decode("utf-8")
        one_day_ago = datetime.now(tz.UTC) - timedelta(hours=24)

        stati = ["COMPLETED", "SAVED", "HADOOP RUNNING", "HADOOP FAILED"]
        return (status in stati) and (
            one_day_ago <= last_modified_datetime <= datetime.now(tz.UTC)
        )


class IntegratedAlertsSync(Sync):
    """
    Defines jobs to create new integrated alerts assets once a source alert dataset is updated.
    """

    DATASET_NAME = "gfw_integrated_alerts"
    SOURCE_DATASETS = [
        "umd_glad_landsat_alerts",
        "umd_glad_sentinel2_alerts",
        "wur_radd_alerts",
    ]
    MULTI_BAND_CALC = "np.ma.array([(A > 20000) * (A != 30000) * (A < 40000) * (2 * (A - (20000 + (A>30000) * 10000)) + (A<30000) * 1), (B > 20000) * (B != 30000) * (B < 40000) * (2 * (B - (20000 + (B>30000) * 10000)) + (B<30000) * 1), (C > 20000) * (C != 30000) * (C < 40000) * (2 * (C - (20000 + (C>30000) * 10000)) + (C<30000) * 1)])"
    SINGLE_BAND_CALC = "np.ma.sum([np.clip(np.ma.sum([(np.ma.sum([(np.ma.masked_equal(A,0)>0)*1,(np.ma.masked_equal(B,0)>0)*1,(np.ma.masked_equal(C,0)>0)*1],axis=0)>=2)*4,(np.ma.sum([np.ma.masked_equal(A,0)&1,np.ma.masked_equal(B,0)&1,np.ma.masked_equal(C,0)&1],axis=0)==0)*3,(np.ma.sum([np.ma.masked_equal(A,0)&1,np.ma.masked_equal(B,0)&1,np.ma.masked_equal(C,0)&1],axis=0)==1)*2],axis=0),None,4).filled(0)*10000,np.ma.min([np.ma.masked_equal(A,0)>>1,np.ma.masked_equal(B,0)>>1,np.ma.masked_equal(C,0)>>1],axis=0)],axis=0).filled(0)"

    def __init__(self, sync_version: str):
        self.sync_version = sync_version

    def build_jobs(self, config: DatapumpConfig) -> List[Job]:
        """
        Create two jobs for sync:
        1) Create integrated raster layers and assets. This includes
            1) Multiband raster where each band is a source dataset with encoded date and confidence
            2) A tile cache, using a special date_conf_intensity_multi_8 to keep information about
                all layers in the PNGs
            3) a single band aux asset with standard date_conf encoding of the first observed alert date
                and integrated confidence, to be used for OTF
        2) Geotrellis job for integrated alerts. This can be done in parallel, since it just uses the
            source datasets directly as well.
        """

        latest_versions = self._get_latest_versions()
        source_uris = [
            f"s3://{GLOBALS.s3_bucket_data_lake}/{dataset}/{version}/raster/epsg-4326/10/100000/date_conf/geotiff/tiles.geojson"
            for dataset, version in latest_versions.items()
        ]

        if self._should_update(latest_versions):
            jobs = []

            if config.dataset == "gadm":
                jobs.append(
                    RasterVersionUpdateJob(
                        id=str(uuid1()),
                        status=JobStatus.starting,
                        dataset=self.DATASET_NAME,
                        version=self.sync_version,
                        tile_set_parameters=RasterTileSetParameters(
                            source_uri=source_uris,
                            calc=self.MULTI_BAND_CALC,
                            grid="10/100000",
                            data_type="uint16",
                            no_data=[0, 0, 0],
                            pixel_meaning="date_conf_v2",
                            band_count=3,
                            union_bands=True,
                            compute_stats=False,
                            timeout_sec=21600,
                        ),
                        tile_cache_parameters=RasterTileCacheParameters(
                            max_zoom=14,
                            symbology={"type": "date_conf_intensity_multi_8"},
                        ),
                        aux_tile_set_parameters=[
                            RasterTileSetParameters(
                                calc=self.SINGLE_BAND_CALC,
                                grid="10/100000",
                                data_type="uint16",
                                pixel_meaning="date_conf",
                                compute_stats=False,
                                timeout_sec=21600,
                            )
                        ],
                    )
                )

            jobs.append(
                GeotrellisJob(
                    id=str(uuid1()),
                    status=JobStatus.starting,
                    analysis_version=config.analysis_version,
                    sync_version=self.sync_version,
                    sync_type=config.sync_type,
                    table=AnalysisInputTable(
                        dataset=config.dataset,
                        version=config.dataset_version,
                        analysis=config.analysis,
                    ),
                    features_1x1=config.metadata["features_1x1"],
                    geotrellis_version=config.metadata["geotrellis_version"],
                )
            )

            return jobs
        else:
            return []

    def _get_latest_versions(self) -> Dict[str, str]:
        client = DataApiClient()
        return {ds: client.get_latest_version(ds) for ds in self.SOURCE_DATASETS}

    def _should_update(self, latest_versions: Dict[str, str]) -> bool:
        """
        Check if any of the dependent deforestation alert layers have created
        a new version in the last 24 hours on the API
        """
        client = DataApiClient()

        versions = [
            client.get_version(ds, latest_versions[ds]) for ds in self.SOURCE_DATASETS
        ]
        last_updates = [
            datetime.fromisoformat(v["created_on"]).replace(tzinfo=tz.UTC)
            for v in versions
        ]

        one_day_ago = datetime.now(tz.UTC) - timedelta(hours=24)

        if any([last_update > one_day_ago for last_update in last_updates]):
            return True

        return False


class RWAreasSync(Sync):
    def __init__(self, sync_version: str):
        self.sync_version = sync_version
        self.features_1x1 = create_1x1_tsv(sync_version)

    def build_jobs(self, config: DatapumpConfig) -> List[Job]:
        if self.features_1x1:
            kwargs = {
                "id": str(uuid1()),
                "status": JobStatus.starting,
                "analysis_version": config.analysis_version,
                "sync_version": self.sync_version,
                "table": AnalysisInputTable(
                    dataset=config.dataset,
                    version=config.dataset_version,
                    analysis=config.analysis,
                ),
                "features_1x1": self.features_1x1,
                "geotrellis_version": config.metadata["geotrellis_version"],
                "sync_type": config.sync_type,
                "version_overrides": config.metadata.get("version_overrides", {}),
            }

            if config.analysis in FIRES_ANALYSES:
                kwargs["alert_type"] = config.analysis
                return [FireAlertsGeotrellisJob(**kwargs)]
            else:
                return [GeotrellisJob(**kwargs)]
        else:
            return []


class Syncer:
    SYNCERS: Dict[SyncType, Type[Sync]] = {
        SyncType.viirs: ViirsSync,
        SyncType.modis: ModisSync,
        SyncType.rw_areas: RWAreasSync,
        SyncType.glad: GladSync,
        SyncType.integrated_alerts: IntegratedAlertsSync,
    }

    def __init__(self, sync_types: List[SyncType], sync_version: str = None):
        self.sync_version: str = (
            sync_version if sync_version else self._get_latest_version()
        )
        self.syncers: Dict[SyncType, Sync] = {
            sync_type: self.SYNCERS[sync_type](self.sync_version)
            for sync_type in sync_types
        }

    @staticmethod
    def _get_latest_version():
        return f"v{datetime.now().strftime('%Y%m%d')}"

    def build_jobs(self, config: DatapumpConfig) -> List[Job]:
        """
        Build Job model based on sync type
        :param config: sync configuration
        :return: Job model, or None if there's no job to sync
        """
        sync_type = SyncType[config.sync_type]
        return self.syncers[sync_type].build_jobs(config)
