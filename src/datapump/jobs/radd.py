from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from ..clients.data_api import DataApiClient
from ..commands import ImportCommand
from ..globals import GLOBALS, LOGGER
from ..jobs.jobs import Job, JobStatus, JobStep
from ..util.exceptions import DataApiResponseError


class RADDJobStep(str, Enum):
    starting = "starting"
    creating_tile_set = "creating_tile_set"
    creating_tile_cache = "creating_tile_cache"
    creating_aux_assets = "creating_aux_assets"
    mark_latest = "mark_latest"


class RADDJob(Job):
    status: JobStatus
    dataset: str
    version: str
    source_uri: List[str]
    calc: Optional[str]
    grid: str
    max_zoom: int

    def next_step(self):
        if self.step == RADDJobStep.starting:
            self.status = JobStatus.executing
            self.step = RADDJobStep.creating_tile_set
            self._create_tile_set()

        elif self.step == RADDJobStep.creating_tile_set:
            status = self._check_tile_set_status()
            if status == JobStatus.complete:
                self.step = RADDJobStep.creating_tile_cache
                self._create_tile_cache()
            elif status == JobStatus.failed:
                self.status = JobStatus.failed

        elif self.step == RADDJobStep.creating_tile_cache:
            status = self._check_tile_cache_status()
            if status == JobStatus.complete:
                self.step = RADDJobStep.creating_aux_assets
                self._create_aux_assets()
            elif status == JobStatus.failed:
                self.status = JobStatus.failed

        elif self.step == RADDJobStep.creating_aux_assets:
            status = self._check_aux_assets_status()
            if status == JobStatus.complete:
                self.step = RADDJobStep.mark_latest
                self._mark_latest()
            elif status == JobStatus.failed:
                self.status = JobStatus.failed

        elif self.step == RADDJobStep.mark_latest:
            status = self._check_latest_status()
            if status == JobStatus.complete:
                self.status = JobStatus.complete
            elif status == JobStatus.failed:
                self.status = JobStatus.failed

    def _create_tile_set(self):
        client = DataApiClient()

        # Create dataset if doesn't exist
        try:
            _ = client.create_dataset(self.dataset)
        except DataApiResponseError:
            pass

        payload = {
            "creation_options": {
                "source_type": "raster",
                # "source_uri": [f"s3://{GLOBALS.s3_data_lake_pipeline}/{dataset}/{version}/raw/tiles.geojson"],
                "source_uri": self.source_uri,
                "source_driver": "GeoTIFF",
                "data_type": "uint16",
                "no_data": 0,
                "pixel_meaning": "date_conf",
                # "grid": "10/100000",
                "grid": self.grid,
                "calc": self.calc
            },
            # "metadata": get_metadata(),
        }
        _ = client.create_raster_version(self.dataset, self.version, payload)

    def _check_tile_set_status(self) -> JobStatus:
        client = DataApiClient()

        rts_asset = client.get_asset(self.dataset, self.version, "Raster tile set")
        if rts_asset["status"] == "saved":
            return JobStatus.complete
        elif rts_asset["status"] == "pending":
            return JobStatus.executing
        else:
            return JobStatus.failed

    def _create_tile_cache(self):
        client = DataApiClient()

        resp = client.get_asset(self.dataset, self.version, "Raster tile set")
        rts_asset_id = resp["asset_id"]

        payload = {
            "asset_type": "Raster tile cache",
            "is_managed": True,
            "creation_options": {
                "source_asset_id": rts_asset_id,
                "min_zoom": 0,
                "max_zoom": self.max_zoom,
                "max_static_zoom": 9,
                "symbology": {"type": "date_conf_intensity"}
            }
        }
        _ = client.create_aux_asset(self.dataset, self.version, payload)

    def _check_tile_cache_status(self) -> JobStatus:
        client = DataApiClient()

        rtc_asset = client.get_asset(self.dataset, self.version, "Raster tile cache")
        if rtc_asset["status"] == "saved":
            return JobStatus.complete
        elif rtc_asset["status"] == "pending":
            return JobStatus.executing
        else:
            return JobStatus.failed

    def _create_aux_assets(self) -> JobStatus:
        # TODO
        pass

    def _check_aux_assets_status(self) -> JobStatus:
        # TODO
        return JobStatus.complete

    def _mark_latest(self):
        client = DataApiClient()

        client.set_latest(self.dataset, self.version)

    def _check_latest_status(self) -> JobStatus:
        client = DataApiClient()

        version_data = client.get_version(self.dataset, self.version)

        if version_data["version"] == self.version:
            return JobStatus.complete
        else:
            return JobStatus.failed
