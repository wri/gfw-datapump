import traceback
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from string import ascii_uppercase
from typing import Dict, List, Optional, Tuple, Type
from uuid import uuid1

import dateutil.tz as tz
from datapump.clients.data_api import DataApiClient

from ..clients.datapump_store import DatapumpConfig
from ..commands.analysis import FIRES_ANALYSES, AnalysisInputTable
from ..commands.sync import SyncType
from ..commands.version_update import RasterTileCacheParameters, RasterTileSetParameters, CogAssetParameters, AuxTileSetParameters
from ..globals import GLOBALS, LOGGER
from ..jobs.geotrellis import FireAlertsGeotrellisJob, GeotrellisJob, Job
from ..jobs.jobs import JobStatus
from ..jobs.version_update import RasterVersionUpdateJob
from ..sync.fire_alerts import process_active_fire_alerts
from ..sync.rw_areas import create_1x1_tsv
from ..util.gcs import get_gs_file_as_text, get_gs_files, get_gs_subfolders
from ..util.models import ContentDateRange
from ..util.util import log_and_notify_error


class Sync(ABC):
    @abstractmethod
    def __init__(self, sync_version: str):
        ...

    @abstractmethod
    def build_jobs(self, config: DatapumpConfig) -> List[Job]:
        ...

    @staticmethod
    def get_latest_api_version(dataset_name: str) -> str:
        """
        Get the version of the latest release in the Data API
        """
        client = DataApiClient()
        return client.get_latest_version(dataset_name)


class FireAlertsSync(Sync):
    def __init__(self, sync_version: str):
        self.sync_version: str = sync_version
        self.fire_alerts_type: Optional[SyncType] = None
        self.fire_alerts_uri: Optional[str] = None
        self.content_end_date: Optional[str] = None

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
                content_end_date=self.content_end_date,
                change_only=True,
                version_overrides=config.metadata.get("version_overrides", {}),
            )
        ]


class ViirsSync(FireAlertsSync):
    def __init__(self, sync_version: str):
        super(ViirsSync, self).__init__(sync_version)
        self.fire_alerts_type = SyncType.viirs
        self.fire_alerts_uri, self.content_end_date = process_active_fire_alerts(
            self.fire_alerts_type.value
        )


class ModisSync(FireAlertsSync):
    def __init__(self, sync_version: str):
        super(ModisSync, self).__init__(sync_version)
        self.fire_alerts_type = SyncType.modis
        self.fire_alerts_uri, self.content_end_date = process_active_fire_alerts(
            self.fire_alerts_type.value
        )


class GladSync(Sync):
    DATASET_NAME = "umd_glad_landsat_alerts"

    def __init__(self, sync_version: str):
        self.sync_version = sync_version

    def build_jobs(self, config: DatapumpConfig) -> List[Job]:
        if self._check_for_new_glad(config):
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
                )
            ]
        else:
            return []

    def _check_for_new_glad(self, config: DatapumpConfig):
        client = DataApiClient()
        glad_tiles_latest_version = client.get_latest_version(self.DATASET_NAME)
        return config.sync_version < glad_tiles_latest_version


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

    # First filter for nodata by multiplying everything by
    # (((A.data) > 0) | ((B.data) > 0) | ((C.data) > 0))
    # Now to establish the combined confidence. We take 10000 and add
    # a maximum of 30000 for multiple alerts, otherwise 10000 for
    # low confidence and 20000 for high confidence single alerts. It looks
    # like taking the max of that and 0 is unnecessary because we already
    # filtered for nodata.
    # Next add the day. We want the minimum (earliest) day of the three
    # systems. Because we can't easily take the minimum of the date and avoid
    # 0 being the nodata value, subtract the day from the maximum 16-bit
    # value (65535) and take the max.
    _INPUT_CALC = """np.ma.array(
        (
            (((A.data) > 0) | ((B.data) > 0) | ((C.data) > 0))
            * (
                10000
                + 10000
                * np.where(
                    ((A.data // 10000) + (B.data // 10000) + (C.data // 10000)) > 3,
                    3,
                    np.maximum(
                        ((A.data // 10000) + (B.data // 10000) + (C.data // 10000)) - 1,
                        0,
                    ),
                ).astype(np.uint16)
                + (
                    65535
                    - np.maximum.reduce(
                        [
                            (
                                ((A.data) > 0)
                                * ((65535 - ((A.data) % 10000)).astype(np.uint16))
                            ),
                            (
                                ((B.data) > 0)
                                * ((65535 - ((B.data) % 10000)).astype(np.uint16))
                            ),
                            (
                                ((C.data) > 0)
                                * ((65535 - ((C.data) % 10000)).astype(np.uint16))
                            ),
                        ]
                    )
                )
            )
        ),
        mask=False,
    )"""
    INPUT_CALC = " ".join(_INPUT_CALC.split())

    def __init__(self, sync_version: str):
        self.sync_version = sync_version

    def build_jobs(self, config: DatapumpConfig) -> List[Job]:
        """
        Creates two jobs for sync:
        1) Creates the integrated raster layers and assets. This includes
            a) A one band raster tile set where the values consist of the date
             of first detection by one of the three alert systems and their
             combined confidence for that pixel.
            b) A tile cache, using the special date_conf_intensity_multi_8 symbology
        2) Creates a Geotrellis job for integrated alerts. This can be done in
         parallel with 1) because it also uses the source datasets directly
        """

        latest_versions = self._get_latest_versions()
        source_uris = [
            f"s3://{GLOBALS.s3_bucket_data_lake}/{dataset}/{version}/raster/epsg-4326/10/100000/date_conf/geotiff/tiles.geojson"
            for dataset, version in latest_versions.items()
        ]

        if not self._should_update(latest_versions):
            return []

        jobs: List[Job] = []

        if config.dataset == "gadm":
            job = RasterVersionUpdateJob(
                id=str(uuid1()),
                status=JobStatus.starting,
                dataset=self.DATASET_NAME,
                version=self.sync_version,
                tile_set_parameters=RasterTileSetParameters(
                    source_uri=source_uris,
                    calc=self.INPUT_CALC,
                    grid="10/100000",
                    data_type="uint16",
                    no_data=0,
                    pixel_meaning="date_conf",
                    band_count=1,
                    union_bands=True,
                    compute_stats=False,
                    # This timeout is about 5-6 hours for the date_conf and intensity
                    # raster jobs (run in series), and then another 6-7 hours for the
                    # default and intensity COG jobs (run in parallel). The
                    # generation of the default COG takes the longest.
                    timeout_sec=13 * 3600,
                ),
                tile_cache_parameters=RasterTileCacheParameters(
                    max_zoom=14,
                    resampling="med",
                    symbology={"type": "date_conf_intensity_multi_8"},
                ),
                content_date_range=ContentDateRange(
                    start_date="2014-12-31", end_date=str(date.today())
                ),
            )
            job.aux_tile_set_parameters = [
                AuxTileSetParameters(
                    source_uri=None,
                    pixel_meaning="intensity",
                    data_type="uint8",
                    calc="(A > 0) * 55",
                    grid="10/100000",
                    no_data=None,
                )
            ]
            job.cog_asset_parameters = [
                # Created from the "date_conf" asset
                CogAssetParameters(
                    source_pixel_meaning="date_conf",
                    resampling="mode",
                    implementation="default",
                    blocksize=1024,
                    # Disable export to GEE until COG metadata is reduced to < 10Mbytes
                    export_to_gee=False,
                ),
                # Created from the "intensity" asset
                CogAssetParameters(
                    source_pixel_meaning="intensity",
                    resampling="bilinear",
                    implementation="intensity",
                    blocksize=1024,
                ),
            ]

            jobs.append(job)

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
                timeout_sec=6 * 3600,
            )
        )

        return jobs

    def _get_latest_versions(self) -> Dict[str, str]:
        client = DataApiClient()
        return {ds: client.get_latest_version(ds) for ds in self.SOURCE_DATASETS}

    def _should_update(self, latest_versions: Dict[str, str]) -> bool:
        """
        See if any of the individual three deforestation alert layers
        have been updated since the latest integrated alert layer
        """
        client = DataApiClient()

        versions = [
            client.get_version(ds, latest_versions[ds]) for ds in self.SOURCE_DATASETS
        ]
        last_updates = [
            datetime.fromisoformat(v["created_on"]).replace(tzinfo=tz.UTC)
            for v in versions
        ]

        latest_integrated_version = client.get_version(
            self.DATASET_NAME, client.get_latest_version(self.DATASET_NAME)
        )

        last_integrated_update = datetime.fromisoformat(
            latest_integrated_version["created_on"]
        ).replace(tzinfo=tz.UTC)

        LOGGER.info(f"Last update time for integrated alerts: {last_integrated_update}")
        LOGGER.info(f"Last update time for source datasets: {last_updates}")

        if any([last_update > last_integrated_update for last_update in last_updates]):
            return True

        return False


class DeforestationAlertsSync(Sync):
    """
    Defines jobs to create new deforestation alerts assets once a new release is available.
    """

    @property
    @abstractmethod
    def dataset_name(self):
        ...

    @property
    @abstractmethod
    def source_bucket(self):
        ...

    @property
    @abstractmethod
    def source_prefix(self):
        ...

    @property
    @abstractmethod
    def input_calc(self):
        ...

    @property
    @abstractmethod
    def number_of_tiles(self):
        ...

    @property
    @abstractmethod
    def grid(self):
        ...

    @property
    @abstractmethod
    def max_zoom(self):
        ...

    def __init__(self, sync_version: str):
        self.sync_version = sync_version

    def build_jobs(self, config: DatapumpConfig) -> List[Job]:
        """
        Creates the deforestation raster layer and assets
        """

        latest_api_version = self.get_latest_api_version(self.dataset_name)
        latest_release, source_uris = self.get_latest_release()

        if float(latest_api_version.lstrip("v")) >= float(latest_release.lstrip("v")):
            return []

        return [self.get_raster_job(latest_release, source_uris)]

    def get_raster_job(
        self, version: str, source_uris: List[str]
    ) -> RasterVersionUpdateJob:
        version_dt: str = str(self.parse_version_as_dt(version).date())

        return RasterVersionUpdateJob(
            id=str(uuid1()),
            status=JobStatus.starting,
            dataset=self.dataset_name,
            version=version,
            tile_set_parameters=RasterTileSetParameters(
                source_uri=source_uris,
                calc=self.input_calc,
                grid=self.grid,
                data_type="uint16",
                no_data=0,
                pixel_meaning="date_conf",
                band_count=1,
                compute_stats=False,
            ),
            tile_cache_parameters=RasterTileCacheParameters(
                max_zoom=self.max_zoom,
                resampling="med",
                symbology={"type": "date_conf_intensity"},
            ),
            content_date_range=ContentDateRange(
                start_date="2020-01-01", end_date=str(version_dt)
            ),
        )

    @abstractmethod
    def get_latest_release(self) -> Tuple[str, List[str]]:
        ...

    @staticmethod
    def parse_version_as_dt(version: str) -> datetime:
        # Technically this has a Y10K bug
        release_date = version.lstrip("v")
        assert len(release_date) == 8, "Possibly malformed version folder name!"
        year, month, day = (
            int(release_date[:4]),
            int(release_date[4:6]),
            int(release_date[6:]),
        )
        return datetime(year, month, day)

    @staticmethod
    def get_today():
        return date.today()

    @staticmethod
    def get_days_since_2015(year: int) -> int:
        year_date = date(year=year, month=1, day=1)
        start_date = date(year=2015, month=1, day=1)
        return (year_date - start_date).days


class RADDAlertsSync(DeforestationAlertsSync):
    """
    Defines jobs to create new RADD alerts assets once a new release is available.
    """

    dataset_name = "wur_radd_alerts"
    source_bucket = "gfw_gee_export"
    source_prefix = "wur_radd_alerts/"
    input_calc = "(A >= 20000) * (A < 40000) * A"
    number_of_tiles = [208, 209]  # Africa:54, Asia:70, CA: 16, SA:68
    grid = "10/100000"
    max_zoom = 14

    def __init__(self, sync_version: str):
        super().__init__(sync_version)

    def build_jobs(self, config: DatapumpConfig) -> List[Job]:
        return super().build_jobs(config)

    def get_latest_release(self) -> Tuple[str, List[str]]:
        """
        Get the version of the latest *complete* release in GCS
        """

        LOGGER.info(
            f"Looking for RADD folders in gs://{self.source_bucket}/{self.source_prefix}"
        )
        versions: List[str] = get_gs_subfolders(self.source_bucket, self.source_prefix)

        # Shouldn't need to look back through many, so avoid the corner
        # case that would check every previous version when run right after
        # increasing NUMBER_OF_TILES and hitting GCS as a new release is being
        # uploaded

        LOGGER.info(f"{self.dataset_name} versions: {versions}")
        for version in sorted(versions, reverse=True)[:3]:
            version_prefix = f"{self.source_prefix}{version}"
            LOGGER.info(
                f"Looking for RADD tiles in gs://{self.source_bucket}/{version_prefix}"
            )

            version_tiles: int = len(
                get_gs_files(self.source_bucket, version_prefix, extensions=[".tif"])
            )

            LOGGER.info(
                f"Found {version_tiles} RADD tiles in gs://{self.source_bucket}/{version_prefix}"
            )
            # Why is self.number_of_tiles a list? Because it seems that it
            # varies a little. For any large change, though, WUR should give
            # us a heads-up and we will update.
            if version_tiles in self.number_of_tiles:
                latest_release = version.rstrip("/")
                source_uris = [
                    f"gs://{self.source_bucket}/{self.source_prefix}{latest_release}"
                ]

                return latest_release, source_uris
            elif all(version_tiles > num for num in self.number_of_tiles):
                raise Exception(
                    f"Found {version_tiles} TIFFs in latest {self.dataset_name}"
                    "GCS folder, which is greater than any of the expected "
                    f"values ({self.number_of_tiles}). "
                    "If the extent has changed, update the number_of_tiles value "
                    f"in the datapump for {self.dataset_name}"
                )

        # We shouldn't get here
        raise Exception(f"No complete {self.dataset_name} versions found in GCS!")


class GLADLAlertsSync(DeforestationAlertsSync):
    """
    Defines jobs to create new GLAD-L alerts assets once a new release is available.
    """

    dataset_name = "umd_glad_landsat_alerts"
    source_bucket = "earthenginepartners-hansen"
    source_prefix = "GLADalert/C2"
    number_of_tiles = 115
    grid = "10/40000"
    start_year = 2021
    max_zoom = 12

    @property
    def input_calc(self):
        """
        Calc string is
        """
        today = self.get_today()

        calc_strings = []
        prev_conf_bands = []
        bands = iter(ascii_uppercase)

        for year in range(self.start_year, today.year + 1):
            year_start = self.get_days_since_2015(year)
            conf_band = next(bands)

            # earlier years should override later years for overlapping pixels
            prev_conf_calc_string = "".join(
                [f"({band} == 0) * " for band in prev_conf_bands]
            )

            date_band = next(bands)
            calc_strings.append(
                f"({prev_conf_calc_string}({conf_band} > 0) * (20000 + 10000 * ({conf_band} > 2) + {year_start} + {date_band}))"
            )
            prev_conf_bands.append(conf_band)

        calc_string = f"np.ma.array({' + '.join(calc_strings)}, mask=False)"
        return calc_string

    def get_raster_job(
        self, version: str, source_uris: List[str]
    ) -> RasterVersionUpdateJob:
        raster_job = super().get_raster_job(version, source_uris)
        raster_job.aux_tile_set_parameters = [
            AuxTileSetParameters(
                grid="10/100000",
                data_type="uint16",
                pixel_meaning="date_conf",
                union_bands=True,
                compute_stats=False,
                timeout_sec=21600,
                no_data=0,
            )
        ]

        return raster_job

    def get_latest_release(self) -> Tuple[str, List[str]]:
        # UMD's GLAD release scheme goes something like this:
        # GLAD alerts are released as a set of tiles that contain all the
        # alerts for a given year, placed in
        # GLADalert/C2/{year_of_release}/{month_day_of_release}
        # They start out as provisional, which means pixel values may be
        # modified following a QA process (with the new values appearing
        # in subsequent releases). At some point (typically around July)
        # there will be some final QA, after which the alerts for the
        # previous year will be put in the GLADalert/C2/{year_of_data}/final
        # folder.
        # There will be some time during which the processing of current
        # year alerts overlaps the processing of the previous year's alerts,
        # but the tiles have the year of the data in the file names to
        # differentiate them (there are two bands/sets of tiles, named
        # like alert{two_digit_year} and alertDate{two_digit_year}).
        # So.
        # For a given year's data, first see if it's already been finalized
        # (i.e. there are tiles in year/final). If not, find the last day it
        # was released as provisional data (which may be today or some time
        # in the past: As of this writing they have stopped including the 2021
        # data in daily updates but have not yet put anything in the "final"
        # folder).
        today = self.get_today()

        source_uris: List[str] = []
        release_version: str = "v" + today.strftime("%Y%m%d")

        for target_year in range(self.start_year, today.year + 1):
            two_digit_year = str(target_year)[-2:]

            tiles: List[str] = get_gs_files(
                self.source_bucket,
                f"{self.source_prefix}/{target_year}/final/alertDate{two_digit_year}",
                extensions=[".tif"],
            )

            if len(tiles) > self.number_of_tiles:
                raise Exception(
                    f"Found {len(tiles)} TIFFs in {self.dataset_name} "
                    "GCS folder, which is greater than the expected "
                    f"{self.number_of_tiles} tiles. If the extent has grown,"
                    "update self.number_of_tiles value."
                )
            if len(tiles) == self.number_of_tiles:
                source_uris += [
                    f"gs://{self.source_bucket}/{self.source_prefix}/{target_year}/final/alert{two_digit_year}*",
                    f"gs://{self.source_bucket}/{self.source_prefix}/{target_year}/final/alertDate{two_digit_year}*",
                ]
                continue

            # We found less than self.number_of_tiles (potentially 0) in the
            # "final" folder, so tiles for the year are still being modified.
            # Step back in history (starting with today) until we find the
            # last day that there was a full set. Stop if we reach a year ago
            # without finding one.
            a_year_ago: date = today - timedelta(days=365)

            search_day: date = today
            search_month_day: str = search_day.strftime("%m_%d")

            tiles = get_gs_files(
                self.source_bucket,
                f"{self.source_prefix}/{search_day.year}/{search_month_day}/alertDate{two_digit_year}",
                extensions=[".tif"],
            )

            while (
                len(tiles) < self.number_of_tiles
                and search_day.year >= target_year
                and search_day > a_year_ago
            ):
                search_day -= timedelta(days=1)
                search_month_day = search_day.strftime("%m_%d")

                tiles = get_gs_files(
                    self.source_bucket,
                    f"{self.source_prefix}/{search_day.year}/{search_month_day}/alertDate{two_digit_year}",
                    extensions=[".tif"],
                )

            if len(tiles) > self.number_of_tiles:
                raise Exception(
                    f"Found {len(tiles)} TIFFs in {self.dataset_name} "
                    "GCS folder, which is greater than the expected "
                    f"{self.number_of_tiles}. "
                    "If the extent has grown, update NUMBER_OF_TILES value."
                )
            if len(tiles) < self.number_of_tiles:
                raise Exception(
                    f"Can't find tiles for {target_year}, even after looking "
                    f"back as far as {search_day.year}/{search_month_day}!"
                )

            # We found them!
            source_uris += [
                f"gs://{self.source_bucket}/{self.source_prefix}/{search_day.year}/{search_month_day}/alert{two_digit_year}*",
                f"gs://{self.source_bucket}/{self.source_prefix}/{search_day.year}/{search_month_day}/alertDate{two_digit_year}*",
            ]

            if two_digit_year == str(today.year)[-2:]:
                release_version = "v" + search_day.strftime("%Y%m%d")

        return release_version, source_uris


class GLADS2AlertsSync(DeforestationAlertsSync):
    """
    Defines jobs to create new GLAD-S2 alerts assets once a new release is available.
    """

    dataset_name = "umd_glad_sentinel2_alerts"
    source_bucket = "earthenginepartners-hansen"
    source_prefix = "S2alert"
    input_calc = "(A > 0) * (20000 + 10000 * (A > 1) + B + 1461)"
    number_of_tiles = 18
    grid = "10/100000"
    max_zoom = 14

    def get_latest_release(self) -> Tuple[str, List[str]]:
        """
        Get the version of the latest *complete* release in GCS
        """

        # Raw tiles are just updated in-place
        source_uri = [
            f"gs://{self.source_bucket}/{self.source_prefix}/alert",
            f"gs://{self.source_bucket}/{self.source_prefix}/alertDate",
        ]

        # This file is updated once tiles are updated
        upload_date_text = get_gs_file_as_text(
            self.source_bucket, f"{self.source_prefix}/uploadDate.txt"
        )

        # Example string: "Updated Fri Apr 15 14:27:01 2022 UTC"
        upload_date = upload_date_text[12:-5]
        LOGGER.info(f"Last GLAD-S2 upload date: {upload_date}")
        latest_release = datetime.strptime(upload_date, "%b %d %H:%M:%S %Y").strftime(
            "v%Y%m%d"
        )

        return latest_release, source_uri


class DISTAlertsSync(Sync):
    """
    Defines jobs to create new DIST alerts assets once a new release is available.
    """

    dataset_name = "umd_glad_dist_alerts"
    source_bucket = "earthenginepartners-hansen"
    source_prefix = "DIST-ALERT"
    input_calc = """
        np.where((A>=30) & (A<255) & (B>0) & (C>=2) & (C<255),
            np.where(C<4, 20000 + B, 30000 + B),
            -1
        )
    """

    def __init__(self, sync_version: str):
        self.sync_version = sync_version

    def get_latest_release(self) -> Tuple[str, List[str]]:
        """
        Get the version of the latest release in GCS
        """

        # Raw tiles are just updated in-place
        source_uris = [
            f"gs://{self.source_bucket}/{self.source_prefix}/VEG-ANOM-MAX",
            f"gs://{self.source_bucket}/{self.source_prefix}/VEG-DIST-DATE",
            f"gs://{self.source_bucket}/{self.source_prefix}/VEG-DIST-COUNT",
        ]

        # This file is updated once tiles are updated
        upload_date_text = get_gs_file_as_text(
            self.source_bucket, f"{self.source_prefix}/uploadDate.txt"
        )

        # Example string: "Updated Sat Nov 9 13:43:05 2024-11-09 UTC"
        upload_date = upload_date_text[-15:-5]
        LOGGER.info(f"Last DIST-Alert upload date: {upload_date}")
        latest_release = f"v{upload_date.replace('-', '')}"

        return latest_release, source_uris
    
    def build_jobs (self, config: DatapumpConfig) -> List[Job]:
        latest_api_version = self.get_latest_api_version(self.dataset_name)
        latest_release, source_uris = self.get_latest_release()

        # If the latest API version matches latest release from UMD, no need to update
        if latest_api_version == latest_release:
            return []
        
        jobs: List[Job] = []

        job = RasterVersionUpdateJob(
            # Current week alerts tile set
            id=str(uuid1()),
            status=JobStatus.starting,
            dataset=self.dataset,
            version=latest_release,
            tile_set_parameters=RasterTileSetParameters(
                source_uri=source_uris,
                calc=self.input_calc,
                grid="10/40000",
                data_type="int16",
                no_data=-1,
                pixel_meaning="currentweek",
                band_count=1,
                compute_stats=False,
                union_bands=True,
                unify_projection=True
            ),
            content_date_range=ContentDateRange(
                start_date="2020-12-31", end_date=str(date.today())
            )
        )
        job.aggregated_tile_set_parameters = AuxTileSetParameters(
            # Aggregated tile set (to include all alerts)
            pixel_meaning="default",
            grid="10/40000",
            data_type="int16",
            no_data=-1,
            calc="np.where(A > 0, A, B)",
            auxiliary_asset_pixel_meaning = "default"
        )
        job.aux_tile_set_parameters = [
            # Intensity tile set
            AuxTileSetParameters(
                source_uri=None,
                pixel_meaning="intensity",
                data_type="uint8",
                calc="(B > 0) * 55",
                grid="10/40000",
                no_data=None,
                auxiliary_asset_pixel_meaning = "default"
            )
        ]
        job.cog_asset_parameters = [
            # Created from the "default" asset
            CogAssetParameters(
                source_pixel_meaning="default",
                resampling="mode",
                implementation="default",
                blocksize=1024,
                export_to_gee=False
            ),
            # Created from the "intensity" asset
            CogAssetParameters(
                source_pixel_meaning="intensity",
                resampling="bilinear",
                implementation="intensity",
                blocksize=1024
            )
        ]

        jobs.append(job)

        return jobs

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
        SyncType.wur_radd_alerts: RADDAlertsSync,
        SyncType.umd_glad_landsat_alerts: GLADLAlertsSync,
        SyncType.umd_glad_sentinel2_alerts: GLADS2AlertsSync,
        SyncType.umd_glad_dist_alerts: DISTAlertsSync,
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
    def _get_latest_version() -> str:
        return f"v{datetime.now().strftime('%Y%m%d')}"

    def build_jobs(self, config: DatapumpConfig) -> List[Job]:
        """
        Build Job model based on sync type
        :param config: sync configuration
        :return: Job model, or None if there's no job to sync
        """
        sync_type = SyncType[config.sync_type]

        try:
            jobs = self.syncers[sync_type].build_jobs(config)
        except Exception:
            error_msg: str = (
                f"Could not generate jobs for sync type {sync_type} "
                f"due to exception: {traceback.format_exc()}"
            )
            _ = log_and_notify_error(f"Unhandled exception building jobs: {error_msg}")
            return []

        return jobs
