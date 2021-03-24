from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Type
from uuid import uuid1

import dateutil.tz as tz

from ..clients.aws import get_s3_client, get_s3_path_parts
from ..clients.datapump_store import DatapumpConfig
from ..commands import AnalysisInputTable, SyncType
from ..globals import GLOBALS
from ..jobs.geotrellis import FireAlertsGeotrellisJob, GeotrellisJob, Job
from ..jobs.jobs import JobStatus
from ..sync.fire_alerts import process_active_fire_alerts
from ..sync.rw_areas import create_1x1_tsv


class Sync(ABC):
    @abstractmethod
    def __init__(self, sync_version: str):
        ...

    @abstractmethod
    def build_job(self, config: DatapumpConfig) -> Optional[Job]:
        ...


class FireAlertsSync(Sync):
    def __init__(self, sync_version: str):
        self.sync_version: str = sync_version
        self.fire_alerts_type: Optional[SyncType] = None
        self.fire_alerts_uri: Optional[str] = None

    def build_job(self, config: DatapumpConfig) -> Optional[Job]:
        if self.fire_alerts_type is None:
            raise RuntimeError("No Alert type set")

        return FireAlertsGeotrellisJob(
            id=str(uuid1()),
            status=JobStatus.starting,
            analysis_version=config.analysis_version,
            sync_version=self.sync_version,
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
        )


class ViirsSync(FireAlertsSync):
    def __init__(self, sync_version: str):
        super(ViirsSync, self).__init__(sync_version)
        self.fire_alerts_type = SyncType.viirs
        # TODO use version name?
        self.fire_alerts_uri = process_active_fire_alerts(self.fire_alerts_type.value)


class ModisSync(FireAlertsSync):
    def __init__(self, sync_version: str):
        super(ModisSync, self).__init__(sync_version)
        self.fire_alerts_type = SyncType.modis
        self.fire_alerts_uri = process_active_fire_alerts(self.fire_alerts_type.value)


class GladSync(Sync):
    def __init__(self, sync_version: str):
        self.sync_version = sync_version
        self.should_sync_glad = self._check_for_new_glad()

    def build_job(self, config: DatapumpConfig) -> Optional[Job]:
        if self.should_sync_glad:
            return GeotrellisJob(
                id=str(uuid1()),
                status=JobStatus.starting,
                analysis_version=config.analysis_version,
                sync_version=self.sync_version,
                table=AnalysisInputTable(
                    dataset=config.dataset,
                    version=config.dataset_version,
                    analysis=config.analysis,
                ),
                features_1x1=config.metadata["features_1x1"],
                geotrellis_version=config.metadata["geotrellis_version"],
                change_only=True,
            )
        else:
            return None

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


class RWAreasSync(Sync):
    def __init__(self, sync_version: str):
        self.sync_version = sync_version
        self.features_1x1 = create_1x1_tsv(sync_version)

    def build_job(self, config: DatapumpConfig) -> Optional[Job]:
        if self.features_1x1:
            return GeotrellisJob(
                id=str(uuid1()),
                status=JobStatus.starting,
                analysis_version=config.analysis_version,
                sync_version=self.sync_version,
                table=AnalysisInputTable(
                    dataset=config.dataset,
                    version=config.dataset_version,
                    analysis=config.analysis,
                ),
                features_1x1=self.features_1x1,
                geotrellis_version=config.metadata["geotrellis_version"],
            )
        else:
            return None


class Syncer:
    SYNCERS: Dict[SyncType, Type[Sync]] = {
        SyncType.viirs: ViirsSync,
        SyncType.modis: ModisSync,
        SyncType.rw_areas: RWAreasSync,
        SyncType.glad: GladSync,
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

    def build_job(self, config: DatapumpConfig) -> Optional[Job]:
        """
        Build Job model based on sync type
        :param config: sync configuration
        :return: Job model, or None if there's no job to sync
        """
        sync_type = SyncType[config.sync_type]
        return self.syncers[sync_type].build_job(config)
