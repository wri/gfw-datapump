from enum import Enum

from datapump.commands.version_update import (
    RasterTileCacheParameters,
    RasterTileSetParameters
)

from ..clients.data_api import DataApiClient
from ..jobs.jobs import Job, JobStatus
from ..util.exceptions import DataApiResponseError


class VersionUpdateJobStep(str, Enum):
    starting = "starting"
    creating_tile_set = "creating_tile_set"
    creating_tile_cache = "creating_tile_cache"
    creating_aux_assets = "creating_aux_assets"
    mark_latest = "mark_latest"


class RasterVersionUpdateJob(Job):
    dataset: str
    version: str

    tile_set_parameters: RasterTileSetParameters
    tile_cache_parameters: RasterTileCacheParameters

    def next_step(self):
        if self.step == VersionUpdateJobStep.starting:
            self.status = JobStatus.executing
            self.step = VersionUpdateJobStep.creating_tile_set
            self._create_tile_set()

        elif self.step == VersionUpdateJobStep.creating_tile_set:
            status = self._check_tile_set_status()
            if status == JobStatus.complete:
                self.step = VersionUpdateJobStep.creating_tile_cache
                self._create_tile_cache()
            elif status == JobStatus.failed:
                self.status = JobStatus.failed

        elif self.step == VersionUpdateJobStep.creating_tile_cache:
            status = self._check_tile_cache_status()
            if status == JobStatus.complete:
                self.step = VersionUpdateJobStep.mark_latest
                self._mark_latest()
            elif status == JobStatus.failed:
                self.status = JobStatus.failed

        elif self.step == VersionUpdateJobStep.mark_latest:
            status = self._check_latest_status()
            if status == JobStatus.complete:
                self.status = JobStatus.complete
            elif status == JobStatus.failed:
                self.status = JobStatus.failed

    def _create_tile_set(self):
        client = DataApiClient()

        co = self.tile_set_parameters

        # Create the dataset if it doesn't exist
        try:
            _ = client.create_dataset(self.dataset)
        except DataApiResponseError:
            pass

        payload = {
            "creation_options": {
                "source_type": "raster",
                "source_uri": co.source_uri,
                "source_driver": "GeoTIFF",
                "data_type": co.data_type,
                "no_data": co.no_data,
                "pixel_meaning": co.pixel_meaning,
                "grid": co.grid,
                "calc": co.calc
            },
        }
        _ = client.create_version(self.dataset, self.version, payload)

    def _check_tile_set_status(self) -> JobStatus:
        client = DataApiClient()

        rts_asset = client.get_asset(
            self.dataset,
            self.version,
            "Raster tile set"
        )
        if rts_asset["status"] == "saved":
            return JobStatus.complete
        elif rts_asset["status"] == "pending":
            return JobStatus.executing
        else:
            return JobStatus.failed

    def _create_tile_cache(self):
        client = DataApiClient()

        rts_asset = client.get_asset(
            self.dataset,
            self.version,
            "Raster tile set"
        )
        rts_asset_id = rts_asset["asset_id"]

        payload = {
            "asset_type": "Raster tile cache",
            "is_managed": True,
            "creation_options": {
                "source_asset_id": rts_asset_id,
                "min_zoom": 0,
                "max_zoom": self.tile_cache_parameters.max_zoom,
                "max_static_zoom": 9,
                "symbology": self.tile_cache_parameters.symbology
            }
        }
        _ = client.create_aux_asset(self.dataset, self.version, payload)

    def _check_tile_cache_status(self) -> JobStatus:
        client = DataApiClient()

        rtc_asset = client.get_asset(
            self.dataset,
            self.version,
            "Raster tile cache"
        )
        if rtc_asset["status"] == "saved":
            return JobStatus.complete
        elif rtc_asset["status"] == "pending":
            return JobStatus.executing
        else:
            return JobStatus.failed

    def _mark_latest(self):
        client = DataApiClient()

        client.set_latest(self.dataset, self.version)

    def _check_latest_status(self) -> JobStatus:
        client = DataApiClient()

        latest_version = client.get_latest_version(self.dataset)

        if latest_version == self.version:
            return JobStatus.complete
        else:
            return JobStatus.failed
