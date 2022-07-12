#############
## Test some specific code paths without having to test the entire step function
#############
import os
import time
from datetime import date, datetime, timedelta
from typing import List

import pytest

os.environ["S3_BUCKET_PIPELINE"] = "gfw-pipelines-test"
os.environ["S3_BUCKET_DATA_LAKE"] = "gfw-data-lake-test"
os.environ["GEOTRELLIS_JAR_PATH"] = "s3://gfw-pipelines-test/geotrellis/jars"

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
    assert step == EXPECTED

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


def test_radd_sync(monkeypatch):
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
        lambda bucket, prefix: ["v20220222", "v20220221", "v20211018", "v20211016"],
    )
    monkeypatch.setattr(
        sync, "get_gs_files", lambda bucket, prefix, **kwargs: list(range(0, 175))
    )

    raster_jobs = RADDAlertsSync("v20220101").build_jobs(mock_dp_config)

    assert raster_jobs
    job = raster_jobs[0]
    assert isinstance(job, RasterVersionUpdateJob)
    assert job.version == "v20220222"
    assert job.content_date_range.max == "2022-02-22"
    assert job.tile_set_parameters.source_uri == [
        "gs://gfw_gee_export/wur_radd_alerts/v20220222"
    ]
    assert job.tile_set_parameters.grid == "10/100000"
    assert job.tile_set_parameters.calc == "(A >= 20000) * (A < 40000) * A"


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

    raster_jobs = GLADS2AlertsSync("v20220223").build_jobs(mock_dp_config)

    assert raster_jobs
    job = raster_jobs[0]
    assert isinstance(job, RasterVersionUpdateJob)
    assert job.version == "v20220222"
    assert job.content_date_range.max == "2022-02-22"
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

    monkeypatch.setattr(
        DeforestationAlertsSync, "get_latest_api_version", lambda x, y: "v20210118"
    )

    raster_jobs = GLADLAlertsSync("v20220222").build_jobs(mock_dp_config)

    assert raster_jobs
    job = raster_jobs[0]
    assert isinstance(job, RasterVersionUpdateJob)
    assert job.version == test_version
    assert job.content_date_range.max == test_date.strftime("%Y-%m-%d")
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

    monkeypatch.setattr(
        DeforestationAlertsSync, "get_latest_api_version", lambda x, y: "v20210118"
    )

    raster_jobs = GLADLAlertsSync("v20220222").build_jobs(mock_dp_config)

    assert raster_jobs
    job = raster_jobs[0]
    assert isinstance(job, RasterVersionUpdateJob)
    assert job.version == test_version
    assert job.content_date_range.max == test_date.strftime("%Y-%m-%d")
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

    monkeypatch.setattr(
        DeforestationAlertsSync, "get_latest_api_version", lambda x, y: "v20210118"
    )

    raster_jobs = GLADLAlertsSync("v20220222").build_jobs(mock_dp_config)

    assert raster_jobs
    job = raster_jobs[0]
    assert isinstance(job, RasterVersionUpdateJob)
    assert job.version == test_version
    assert job.content_date_range.max == test_date.strftime("%Y-%m-%d")
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

    monkeypatch.setattr(
        DeforestationAlertsSync, "get_latest_api_version", lambda x, y: "v20210118"
    )

    raster_jobs = GLADLAlertsSync("v20220222").build_jobs(mock_dp_config)

    assert raster_jobs
    job = raster_jobs[0]
    assert isinstance(job, RasterVersionUpdateJob)
    assert job.version == test_version
    assert job.content_date_range.max == test_date.strftime("%Y-%m-%d")
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
