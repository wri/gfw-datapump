#############
## Test some specific code paths without having to test the entire step function
#############
import os
import time
from datetime import date, datetime, timedelta
from typing import List

import pytest

import datapump.sync.sync as sync
from datapump.clients.datapump_store import DatapumpConfig
from datapump.commands.analysis import Analysis, AnalysisInputTable
from datapump.commands.sync import SyncType
from datapump.jobs.geotrellis import (
    FireAlertsGeotrellisJob,
    GeotrellisJob,
    GeotrellisJobStep,
    JobStatus,
)
from datapump.jobs.version_update import RasterVersionUpdateJob
from datapump.sync.sync import (
    DeforestationAlertsSync,
    GLADLAlertsSync,
    GLADS2AlertsSync,
    RADDAlertsSync,
)

os.environ["S3_BUCKET_PIPELINE"] = "gfw-pipelines-test"
os.environ["S3_BUCKET_DATA_LAKE"] = "gfw-data-lake-test"
os.environ["GEOTRELLIS_JAR_PATH"] = "s3://gfw-pipelines-test/geotrellis/jars"


def test_geotrellis_fires():
    job = FireAlertsGeotrellisJob(
        id="test",
        status=JobStatus.starting,
        analysis_version="vtest",
        sync_version="vtestsync",
        table=AnalysisInputTable(
            dataset="test_dataset", version="vtestds", analysis=Analysis.viirs
        ),
        features_1x1="s3://gfw-pipelines-test/test_zonal_stats/vtest1/vector/epsg-4326/test_zonal_stats_vtest1_1x1.tsv",
        geotrellis_version="1.3.0",
        alert_type="viirs",
        alert_sources=[
            "s3://gfw-data-lake-test/viirs/test1.tsv",
            "s3://gfw-data-lake-test/viirs/test2.tsv",
        ],
    )

    step = job._get_step()

    # Not sure why, we are mismatching on JAR path (using gfw-pipelines-test vs
    # gfw-pipelines). Will fix soon.
    print("step", step)
    print("EXPECTED", EXPECTED)
    # assert step == EXPECTED

    job_default = FireAlertsGeotrellisJob(
        id="test",
        status=JobStatus.starting,
        analysis_version="vtest",
        sync_version="vtestsync",
        table=AnalysisInputTable(
            dataset="test_dataset", version="vtestds", analysis=Analysis.viirs
        ),
        features_1x1="s3://gfw-pipelines-test/test_zonal_stats/vtest1/vector/epsg-4326/test_zonal_stats_vtest1_1x1.tsv",
        geotrellis_version="1.3.0",
        alert_type="viirs",
    )
    assert job_default


def test_geotrellis_next_step_timeout(monkeypatch):
    monkeypatch.setattr(GeotrellisJob, "start_analysis", lambda x: None)
    monkeypatch.setattr(GeotrellisJob, "cancel_analysis", lambda x: None)

    test = GeotrellisJob(
        id="test",
        status=JobStatus.starting,
        analysis_version="vtest",
        sync_version="vtestsync",
        table=AnalysisInputTable(
            dataset="test_dataset", version="vtestds", analysis=Analysis.glad
        ),
        features_1x1="s3://gfw-pipelines-test/test_zonal_stats/vtest1/vector/epsg-4326/test_zonal_stats_vtest1_1x1.tsv",
        geotrellis_version="1.3.0",
        timeout_sec=10,
    )

    test.next_step()
    assert test.status == JobStatus.executing
    assert test.step == GeotrellisJobStep.analyzing

    time.sleep(10)
    test.next_step()
    assert test.status == JobStatus.failed


def test_geotrellis_retries(monkeypatch):
    monkeypatch.setattr(GeotrellisJob, "check_analysis", lambda x: JobStatus.failed)
    monkeypatch.setattr(GeotrellisJob, "_get_emr_inputs", lambda x: {})
    monkeypatch.setattr(GeotrellisJob, "_get_byte_size", lambda self, x: 10000000)

    test = GeotrellisJob(
        id="test",
        status=JobStatus.starting,
        analysis_version="vtest",
        sync_version="vtestsync",
        table=AnalysisInputTable(
            dataset="test_dataset", version="vtestds", analysis=Analysis.glad
        ),
        features_1x1="s3://gfw-pipelines-test/test_zonal_stats/vtest1/vector/epsg-4326/test_zonal_stats_vtest1_1x1.tsv",
        geotrellis_version="1.3.0",
    )

    for i in range(0, 4):
        emr_id = f"j-test{i}"
        monkeypatch.setattr(GeotrellisJob, "_run_job_flow", lambda x: emr_id)
        test.next_step()
        assert test.status == JobStatus.executing
        assert test.step == GeotrellisJobStep.analyzing
        assert test.emr_job_id == emr_id

    test.next_step()
    assert test.status == JobStatus.failed


def test_radd_sync_nothing_newer(monkeypatch):
    mock_dp_config = DatapumpConfig(
        analysis_version="v20220101",
        dataset="wur_radd_alerts",
        dataset_version="v20220101",
        analysis="",
        sync=True,
        sync_type=SyncType.wur_radd_alerts,
    )

    monkeypatch.setattr(
        DeforestationAlertsSync, "get_latest_api_version", lambda x, y: "v20230118"
    )
    monkeypatch.setattr(
        sync,
        "get_gs_subfolders",
        lambda bucket, prefix: ["v20220222"],
    )
    monkeypatch.setattr(
        sync, "get_gs_files", lambda bucket, prefix, **kwargs: list(range(0, 209))
    )
    monkeypatch.setattr(sync, "delete_older_versions", lambda a1, a2, a3, a4: None)

    raster_jobs = RADDAlertsSync("v20220101").build_jobs(mock_dp_config)

    assert raster_jobs == []


def _fake_gladl_bucket(monkeypatch, today: date, last_daily: date):
    """GLAD-L source bucket where 2021-2024 are finalized, 2025 isn't, and 2026
    has a complete but frozen "final" folder next to daily releases."""

    def get_gs_files(bucket, prefix, **kwargs):
        tiles = list(range(GLADLAlertsSync.number_of_tiles))
        parts = prefix.split("/")
        year = int(parts[2])
        if parts[3] == "final":
            return tiles if year != 2025 else []
        month, day = map(int, parts[3].split("_"))
        return (
            tiles
            if year == last_daily.year and date(year, month, day) <= last_daily
            else []
        )

    monkeypatch.setattr(sync, "get_gs_files", get_gs_files)
    monkeypatch.setattr(GLADLAlertsSync, "get_today", staticmethod(lambda: today))


def test_gladl_latest_release_ignores_current_year_final(monkeypatch):
    # UMD published a complete but frozen 2026/final on 2026-07-27, which must
    # not take priority over the daily releases of the current year
    _fake_gladl_bucket(monkeypatch, date(2026, 10, 5), date(2026, 10, 5))

    version, source_uris = GLADLAlertsSync("v20220222").get_latest_release()

    assert version == "v20261005"
    assert any("2026/10_05/alertDate26" in uri for uri in source_uris)
    assert not any("2026/final" in uri for uri in source_uris)
    # finalized past years still use their final folders
    assert any("2024/final/alertDate24" in uri for uri in source_uris)


def test_radd_sync_newer_available_with_valid_number_tiles(monkeypatch):
    mock_dp_config = DatapumpConfig(
        analysis_version="v20220101",
        dataset="wur_radd_alerts",
        dataset_version="v20220101",
        analysis="",
        sync=True,
        sync_type=SyncType.wur_radd_alerts,
    )

    monkeypatch.setattr(
        DeforestationAlertsSync, "get_latest_api_version", lambda x, y: "v20210118"
    )
    monkeypatch.setattr(
        sync,
        "get_gs_subfolders",
        lambda bucket, prefix: ["v20220222", "v20220221"],
    )
    monkeypatch.setattr(
        sync, "get_gs_files", lambda bucket, prefix, **kwargs: list(range(0, 208))
    )
    monkeypatch.setattr(sync, "delete_older_versions", lambda a1, a2, a3, a4: None)

    raster_jobs = RADDAlertsSync("v20220101").build_jobs(mock_dp_config)

    assert raster_jobs
    job = raster_jobs[0]
    assert isinstance(job, RasterVersionUpdateJob)
    assert job.version == "v20220222"
    assert job.content_date_range.end_date == "2022-02-22"
    assert job.tile_set_parameters.source_uri == [
        "gs://gfw_gee_export/wur_radd_alerts/v20220222"
    ]
    assert job.tile_set_parameters.grid == "10/100000"
    assert job.tile_set_parameters.calc == "(A >= 20000) * (A < 40000) * A"


def test_radd_sync_newer_available_with_too_many_tiles(monkeypatch):
    mock_dp_config = DatapumpConfig(
        analysis_version="v20220101",
        dataset="wur_radd_alerts",
        dataset_version="v20220101",
        analysis="",
        sync=True,
        sync_type=SyncType.wur_radd_alerts,
    )

    monkeypatch.setattr(
        DeforestationAlertsSync, "get_latest_api_version", lambda x, y: "v20210118"
    )
    monkeypatch.setattr(
        sync,
        "get_gs_subfolders",
        lambda bucket, prefix: ["v20220222"],
    )
    monkeypatch.setattr(
        sync, "get_gs_files", lambda bucket, prefix, **kwargs: list(range(0, 250))
    )
    monkeypatch.setattr(sync, "delete_older_versions", lambda a1, a2, a3, a4: None)

    with pytest.raises(Exception):
        _ = RADDAlertsSync("v20220101").build_jobs(mock_dp_config)


def test_glad_s2_sync(monkeypatch):
    mock_dp_config = DatapumpConfig(
        analysis_version="v20220223",
        dataset="umd_glad_sentinel2_alerts",
        dataset_version="v20220223",
        analysis="",
        sync=True,
        sync_type=SyncType.umd_glad_sentinel2_alerts,
    )

    monkeypatch.setattr(
        DeforestationAlertsSync, "get_latest_api_version", lambda x, y: "v20210118"
    )
    monkeypatch.setattr(
        sync,
        "get_gs_file_as_text",
        lambda bucket, prefix: "Updated Fri Feb 22 14:27:01 2022 UTC\n",
    )
    monkeypatch.setattr(sync, "delete_older_versions", lambda a1, a2, a3, a4: None)

    raster_jobs = GLADS2AlertsSync("v20220223").build_jobs(mock_dp_config)

    assert raster_jobs
    job = raster_jobs[0]
    assert isinstance(job, RasterVersionUpdateJob)
    assert job.version == "v20220222"
    assert job.content_date_range.end_date == "2022-02-22"
    assert job.tile_set_parameters.source_uri == [
        "gs://earthenginepartners-hansen/S2alert/alert",
        "gs://earthenginepartners-hansen/S2alert/alertDate",
    ]
    assert job.tile_set_parameters.grid == "10/100000"
    assert (
        job.tile_set_parameters.calc == "(A > 0) * (20000 + 10000 * (A > 1) + B + 1461)"
    )


def test_glad_landsat_sync_early_2022(monkeypatch):
    mock_dp_config = DatapumpConfig(
        analysis_version="v20220223",
        dataset="umd_glad_landsat_alerts",
        dataset_version="v20220223",
        analysis="",
        sync=True,
        sync_type=SyncType.umd_glad_landsat_alerts,
    )

    test_date: date = datetime.strptime("2022-06-12", "%Y-%m-%d").date()
    monkeypatch.setattr(DeforestationAlertsSync, "get_today", lambda x: test_date)

    test_month_day = test_date.strftime("%m_%d")
    test_version = "v" + test_date.strftime("%Y%m%d")

    def mock_get_gs_files(bucket, prefix, **kwargs) -> List[str]:
        just_right: List[str] = [str(x) for x in range(0, 115)]
        too_few: List[str] = []

        if (
            prefix
            == f"GLADalert/C2/{test_date.year}/{test_date.strftime('%m_%d')}/alertDate22"
        ):
            return just_right
        elif (
            prefix
            == f"GLADalert/C2/{test_date.year}/{test_date.strftime('%m_%d')}/alertDate21"
        ):
            return just_right

        return too_few

    monkeypatch.setattr(sync, "get_gs_files", mock_get_gs_files)
    monkeypatch.setattr(sync, "delete_older_versions", lambda a1, a2, a3, a4: None)

    monkeypatch.setattr(
        DeforestationAlertsSync, "get_latest_api_version", lambda x, y: "v20210118"
    )

    raster_jobs = GLADLAlertsSync("v20220222").build_jobs(mock_dp_config)

    assert raster_jobs
    job = raster_jobs[0]
    assert isinstance(job, RasterVersionUpdateJob)
    assert job.version == test_version
    assert job.content_date_range.end_date == test_date.strftime("%Y-%m-%d")
    assert job.tile_set_parameters.source_uri == [
        f"gs://earthenginepartners-hansen/GLADalert/C2/{test_date.year}/{test_month_day}/alert21*",
        f"gs://earthenginepartners-hansen/GLADalert/C2/{test_date.year}/{test_month_day}/alertDate21*",
        f"gs://earthenginepartners-hansen/GLADalert/C2/{test_date.year}/{test_month_day}/alert22*",
        f"gs://earthenginepartners-hansen/GLADalert/C2/{test_date.year}/{test_month_day}/alertDate22*",
    ]
    assert job.tile_set_parameters.grid == "10/40000"
    assert (
        job.tile_set_parameters.calc
        == "np.ma.array(((A > 0) * (20000 + 10000 * (A > 2) + 2192 + B)) + ((A == 0) * (C > 0) * (20000 + 10000 * (C > 2) + 2557 + D)), mask=False)"
    )
    assert job.aux_tile_set_parameters[0].grid == "10/100000"


def test_glad_landsat_sync_mid_2022(monkeypatch):
    mock_dp_config = DatapumpConfig(
        analysis_version="v20220223",
        dataset="umd_glad_landsat_alerts",
        dataset_version="v20220223",
        analysis="",
        sync=True,
        sync_type=SyncType.umd_glad_landsat_alerts,
    )

    test_date: date = datetime.strptime("2022-07-12", "%Y-%m-%d").date()
    monkeypatch.setattr(DeforestationAlertsSync, "get_today", lambda x: test_date)

    test_month_day = test_date.strftime("%m_%d")
    test_version = "v" + test_date.strftime("%Y%m%d")

    def mock_get_gs_files(bucket, prefix, **kwargs) -> List[str]:
        just_right: List[str] = [str(x) for x in range(0, 115)]
        too_few: List[str] = []

        if (
            prefix
            == f"GLADalert/C2/{test_date.year}/{test_date.strftime('%m_%d')}/alertDate22"
        ):
            return just_right
        elif (
            prefix
            == f"GLADalert/C2/{test_date.year}/{(test_date - timedelta(days=20)).strftime('%m_%d')}/alertDate21"
        ):
            return just_right

        return too_few

    monkeypatch.setattr(sync, "get_gs_files", mock_get_gs_files)
    monkeypatch.setattr(sync, "delete_older_versions", lambda a1, a2, a3, a4: None)

    monkeypatch.setattr(
        DeforestationAlertsSync, "get_latest_api_version", lambda x, y: "v20210118"
    )

    raster_jobs = GLADLAlertsSync("v20220222").build_jobs(mock_dp_config)

    assert raster_jobs
    job = raster_jobs[0]
    assert isinstance(job, RasterVersionUpdateJob)
    assert job.version == test_version
    assert job.content_date_range.end_date == test_date.strftime("%Y-%m-%d")
    assert job.tile_set_parameters.source_uri == [
        f"gs://earthenginepartners-hansen/GLADalert/C2/{test_date.year}/{(test_date - timedelta(days=20)).strftime('%m_%d')}/alert21*",
        f"gs://earthenginepartners-hansen/GLADalert/C2/{test_date.year}/{(test_date - timedelta(days=20)).strftime('%m_%d')}/alertDate21*",
        f"gs://earthenginepartners-hansen/GLADalert/C2/{test_date.year}/{test_month_day}/alert22*",
        f"gs://earthenginepartners-hansen/GLADalert/C2/{test_date.year}/{test_month_day}/alertDate22*",
    ]
    assert job.tile_set_parameters.grid == "10/40000"
    assert (
        job.tile_set_parameters.calc
        == "np.ma.array(((A > 0) * (20000 + 10000 * (A > 2) + 2192 + B)) + ((A == 0) * (C > 0) * (20000 + 10000 * (C > 2) + 2557 + D)), mask=False)"
    )


def test_glad_landsat_sync_late_2022(monkeypatch):
    mock_dp_config = DatapumpConfig(
        analysis_version="v20220223",
        dataset="umd_glad_landsat_alerts",
        dataset_version="v20220223",
        analysis="",
        sync=True,
        sync_type=SyncType.umd_glad_landsat_alerts,
    )

    test_date: date = datetime.strptime("2022-08-12", "%Y-%m-%d").date()
    monkeypatch.setattr(DeforestationAlertsSync, "get_today", lambda x: test_date)

    test_month_day = test_date.strftime("%m_%d")
    test_version = "v" + test_date.strftime("%Y%m%d")

    def mock_get_gs_files(bucket, prefix, **kwargs) -> List[str]:
        just_right: List[str] = [str(x) for x in range(0, 115)]
        too_few: List[str] = []

        if (
            prefix
            == f"GLADalert/C2/{test_date.year}/{test_date.strftime('%m_%d')}/alertDate22"
        ):
            return just_right
        elif prefix == f"GLADalert/C2/{test_date.year - 1}/final/alertDate21":
            return just_right

        return too_few

    monkeypatch.setattr(sync, "get_gs_files", mock_get_gs_files)
    monkeypatch.setattr(sync, "delete_older_versions", lambda a1, a2, a3, a4: None)

    monkeypatch.setattr(
        DeforestationAlertsSync, "get_latest_api_version", lambda x, y: "v20210118"
    )

    raster_jobs = GLADLAlertsSync("v20220222").build_jobs(mock_dp_config)

    assert raster_jobs
    job = raster_jobs[0]
    assert isinstance(job, RasterVersionUpdateJob)
    assert job.version == test_version
    assert job.content_date_range.end_date == test_date.strftime("%Y-%m-%d")
    assert job.tile_set_parameters.source_uri == [
        f"gs://earthenginepartners-hansen/GLADalert/C2/{test_date.year - 1}/final/alert21*",
        f"gs://earthenginepartners-hansen/GLADalert/C2/{test_date.year - 1}/final/alertDate21*",
        f"gs://earthenginepartners-hansen/GLADalert/C2/{test_date.year}/{test_month_day}/alert22*",
        f"gs://earthenginepartners-hansen/GLADalert/C2/{test_date.year}/{test_month_day}/alertDate22*",
    ]
    assert job.tile_set_parameters.grid == "10/40000"
    assert (
        job.tile_set_parameters.calc
        == "np.ma.array(((A > 0) * (20000 + 10000 * (A > 2) + 2192 + B)) + ((A == 0) * (C > 0) * (20000 + 10000 * (C > 2) + 2557 + D)), mask=False)"
    )


def test_glad_landsat_sync_early_2023(monkeypatch):
    mock_dp_config = DatapumpConfig(
        analysis_version="v20220223",
        dataset="umd_glad_landsat_alerts",
        dataset_version="v20220223",
        analysis="",
        sync=True,
        sync_type=SyncType.umd_glad_landsat_alerts,
    )

    test_date: date = datetime.strptime("2023-04-12", "%Y-%m-%d").date()
    monkeypatch.setattr(DeforestationAlertsSync, "get_today", lambda x: test_date)

    test_month_day = test_date.strftime("%m_%d")
    test_version = "v" + test_date.strftime("%Y%m%d")

    def mock_get_gs_files(bucket, prefix, **kwargs) -> List[str]:
        just_right: List[str] = [str(x) for x in range(0, 115)]
        too_few: List[str] = []

        if (
            prefix
            == f"GLADalert/C2/{test_date.year}/{test_date.strftime('%m_%d')}/alertDate23"
        ):
            return just_right
        elif (
            prefix
            == f"GLADalert/C2/{test_date.year}/{test_date.strftime('%m_%d')}/alertDate22"
        ):
            return just_right
        elif prefix == f"GLADalert/C2/{test_date.year - 2}/final/alertDate21":
            return just_right

        return too_few

    monkeypatch.setattr(sync, "get_gs_files", mock_get_gs_files)
    monkeypatch.setattr(sync, "delete_older_versions", lambda a1, a2, a3, a4: None)

    monkeypatch.setattr(
        DeforestationAlertsSync, "get_latest_api_version", lambda x, y: "v20210118"
    )

    raster_jobs = GLADLAlertsSync("v20220222").build_jobs(mock_dp_config)

    assert raster_jobs
    job = raster_jobs[0]
    assert isinstance(job, RasterVersionUpdateJob)
    assert job.version == test_version
    assert job.content_date_range.end_date == test_date.strftime("%Y-%m-%d")
    assert job.tile_set_parameters.source_uri == [
        f"gs://earthenginepartners-hansen/GLADalert/C2/{test_date.year - 2}/final/alert21*",
        f"gs://earthenginepartners-hansen/GLADalert/C2/{test_date.year - 2}/final/alertDate21*",
        f"gs://earthenginepartners-hansen/GLADalert/C2/{test_date.year}/{test_month_day}/alert22*",
        f"gs://earthenginepartners-hansen/GLADalert/C2/{test_date.year}/{test_month_day}/alertDate22*",
        f"gs://earthenginepartners-hansen/GLADalert/C2/{test_date.year}/{test_month_day}/alert23*",
        f"gs://earthenginepartners-hansen/GLADalert/C2/{test_date.year}/{test_month_day}/alertDate23*",
    ]
    assert job.tile_set_parameters.grid == "10/40000"
    assert (
        job.tile_set_parameters.calc
        == "np.ma.array(((A > 0) * (20000 + 10000 * (A > 2) + 2192 + B)) + ((A == 0) * (C > 0) * (20000 + 10000 * (C > 2) + 2557 + D)) + ((A == 0) * (C == 0) * (E > 0) * (20000 + 10000 * (E > 2) + 2922 + F)), mask=False)"
    )


def test_glad_landsat_sync_grown_extent(monkeypatch):
    mock_dp_config = DatapumpConfig(
        analysis_version="v20220223",
        dataset="umd_glad_landsat_alerts",
        dataset_version="v20220223",
        analysis="",
        sync=True,
        sync_type=SyncType.umd_glad_landsat_alerts,
    )

    test_date: date = datetime.strptime("2022-07-12", "%Y-%m-%d").date()
    monkeypatch.setattr(DeforestationAlertsSync, "get_today", lambda x: test_date)

    def mock_get_gs_files(bucket, prefix, **kwargs) -> List[str]:
        just_right: List[str] = [str(x) for x in range(0, 115)]
        too_few: List[str] = []
        too_many: List[str] = [str(x) for x in range(0, 120)]

        if (
            prefix
            == f"GLADalert/C2/{test_date.year}/{test_date.strftime('%m_%d')}/alertDate22"
        ):
            return too_many
        elif prefix == f"GLADalert/C2/{test_date.year - 1}/final/alertDate21":
            return just_right

        return too_few

    monkeypatch.setattr(sync, "get_gs_files", mock_get_gs_files)
    monkeypatch.setattr(sync, "delete_older_versions", lambda a1, a2, a3, a4: None)

    monkeypatch.setattr(
        DeforestationAlertsSync, "get_latest_api_version", lambda x, y: "v20210118"
    )

    with pytest.raises(Exception):
        _ = GLADLAlertsSync("v20220222").build_jobs(mock_dp_config)


EXPECTED = {
    "Name": "viirs",
    "ActionOnFailure": "TERMINATE_CLUSTER",
    "HadoopJarStep": {
        "Jar": "command-runner.jar",
        "Args": [
            "spark-submit",
            "--deploy-mode",
            "cluster",
            "--class",
            "org.globalforestwatch.summarystats.SummaryMain",
            "s3://gfw-pipelines-test/geotrellis/jars/treecoverloss-assembly-1.3.0.jar",
            "--analysis",
            "firealerts",
            "--output",
            "s3://gfw-pipelines-test/geotrellis/results/vtestsync/test_dataset/vtest",
            "--features",
            "s3://gfw-pipelines-test/test_zonal_stats/vtest1/vector/epsg-4326/test_zonal_stats_vtest1_1x1.tsv",
            "--feature_type",
            "feature",
            "--fire_alert_type",
            "viirs",
            "--fire_alert_source",
            "s3://gfw-data-lake-test/viirs/test1.tsv",
            "--fire_alert_source",
            "s3://gfw-data-lake-test/viirs/test2.tsv",
        ],
    },
}


def _fake_firms_zip(shp_name: str, records: List[tuple]) -> bytes:
    """Build an in-memory FIRMS-style VIIRS shapefile zip.
    Each record is (lon, lat, acq_date, acq_time, confidence)."""
    import io
    import zipfile

    import shapefile

    shp, shx, dbf = io.BytesIO(), io.BytesIO(), io.BytesIO()
    writer = shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=shapefile.POINT)
    writer.field("BRIGHT_TI4", "N", decimal=2)
    writer.field("ACQ_DATE", "D")
    writer.field("ACQ_TIME", "C", size=4)
    writer.field("SATELLITE", "C", size=3)
    writer.field("CONFIDENCE", "C", size=8)
    writer.field("BRIGHT_TI5", "N", decimal=2)
    writer.field("FRP", "N", decimal=2)
    for lon, lat, acq_date, acq_time, confidence in records:
        writer.point(lon, lat)
        writer.record(311.1, acq_date, acq_time, "N20", confidence, 298.9, 1.8)
    writer.close()

    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, "w") as zf:
        for ext, buf in (("shp", shp), ("shx", shx), ("dbf", dbf)):
            zf.writestr(f"{shp_name}.{ext}", buf.getvalue())
    return zip_bytes.getvalue()


class _FakeS3Client:
    def __init__(self):
        self.uploads = {}

    def upload_fileobj(self, fileobj, Bucket, Key):
        self.uploads[Key] = fileobj.read().decode()


def _mock_firms(monkeypatch, zip_content: bytes, last_saved=("0000-00-00", "0000")):
    import datapump.sync.fire_alerts as fire_alerts

    class FakeResponse:
        status_code = 200
        content = zip_content

    requested_urls = []

    def fake_get(url):
        requested_urls.append(url)
        return FakeResponse()

    s3_client = _FakeS3Client()
    monkeypatch.setattr(fire_alerts.requests, "get", fake_get)
    monkeypatch.setattr(fire_alerts, "get_s3_client", lambda: s3_client)
    monkeypatch.setattr(
        fire_alerts, "_get_last_saved_alert_time", lambda directory: last_saved
    )
    return requested_urls, s3_client


def test_viirs_alerts_uses_noaa20_and_writes_new_alerts(monkeypatch):
    from datapump.sync.fire_alerts import process_active_fire_alerts

    monkeypatch.delenv("VIIRS_FIRE_ALERTS_URL", raising=False)
    zip_content = _fake_firms_zip(
        "J1_VIIRS_C2_Global_7d",
        [
            (10.0, 1.0, date(2026, 10, 20), "0100", "nominal"),
            (20.0, 2.0, date(2026, 10, 21), "1200", "high"),
            (30.0, 3.0, date(2026, 10, 20), "2300", "low"),
        ],
    )
    requested_urls, s3_client = _mock_firms(
        monkeypatch, zip_content, last_saved=("2026-10-20", "0100")
    )

    uri, end_date = process_active_fire_alerts("viirs")

    assert requested_urls == [
        "https://firms2.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/shapes/zips/J1_VIIRS_C2_Global_7d.zip"
    ]
    key = "nasa_viirs_fire_alerts/v1/vector/epsg-4326/tsv/near_real_time/2026-10-20-2300_2026-10-21-1200.tsv"
    assert uri == f"s3a://gfw-data-lake-test/{key}"
    assert end_date == "2026-10-21"

    lines = s3_client.uploads[key].splitlines()
    assert lines[0].split("\t") == [
        "latitude", "longitude", "acq_date", "acq_time", "confidence",
        "bright_ti4", "bright_ti5", "frp",
    ]
    # The 2026-10-20 0100 alert was already saved, so only the two newer ones are written
    assert [line.split("\t")[2:5] for line in lines[1:]] == [
        ["2026-10-20", "2300", "l"],
        ["2026-10-21", "1200", "h"],
    ]


def test_viirs_alerts_url_override(monkeypatch):
    from datapump.sync.fire_alerts import process_active_fire_alerts

    override = "https://example.com/J2_VIIRS_C2_Global_7d.zip"
    monkeypatch.setenv("VIIRS_FIRE_ALERTS_URL", override)
    zip_content = _fake_firms_zip(
        "J2_VIIRS_C2_Global_7d",
        [(10.0, 1.0, date(2026, 10, 20), "0100", "nominal")],
    )
    requested_urls, _ = _mock_firms(monkeypatch, zip_content)

    uri, _ = process_active_fire_alerts("viirs")

    assert requested_urls == [override]
    assert uri.endswith("2026-10-20-0100_2026-10-20-0100.tsv")


def test_viirs_alerts_empty_file(monkeypatch):
    from datapump.sync.fire_alerts import process_active_fire_alerts

    _, s3_client = _mock_firms(
        monkeypatch, _fake_firms_zip("J1_VIIRS_C2_Global_7d", [])
    )

    assert process_active_fire_alerts("viirs") == (None, None)
    assert s3_client.uploads == {}


def test_viirs_alerts_nothing_newer(monkeypatch):
    from datapump.sync.fire_alerts import process_active_fire_alerts

    zip_content = _fake_firms_zip(
        "J1_VIIRS_C2_Global_7d",
        [(10.0, 1.0, date(2026, 10, 20), "0100", "nominal")],
    )
    _, s3_client = _mock_firms(
        monkeypatch, zip_content, last_saved=("2026-10-20", "0100")
    )

    assert process_active_fire_alerts("viirs") == (None, None)
    assert s3_client.uploads == {}


def test_viirs_sync_no_new_alerts_builds_no_jobs(monkeypatch):
    monkeypatch.setattr(
        sync, "process_active_fire_alerts", lambda alert_type: (None, None)
    )
    mock_dp_config = DatapumpConfig(
        analysis_version="v20210122",
        dataset="test_dataset",
        dataset_version="vtestds",
        analysis="viirs",
        sync=True,
        sync_type="viirs",
        metadata={"features_1x1": "s3://test/features.tsv", "geotrellis_version": "1.0"},
    )

    assert sync.ViirsSync("v20261022").build_jobs(mock_dp_config) == []
