#############
## Test some specific code paths without having to test the entire step function
#############
import os
import time

os.environ["S3_BUCKET_PIPELINE"] = "gfw-pipelines-test"
os.environ["S3_BUCKET_DATA_LAKE"] = "gfw-data-lake-test"
os.environ["GEOTRELLIS_JAR_PATH"] = "s3://gfw-pipelines-test/geotrellis/jars"

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
from datapump.sync.sync import RADDAlertsSync


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

    for i in range(0, 3):
        emr_id = f"j-test{i}"
        monkeypatch.setattr(GeotrellisJob, "_run_job_flow", lambda x: emr_id)
        test.next_step()
        assert test.status == JobStatus.executing
        assert test.step == GeotrellisJobStep.analyzing
        assert test.emr_job_id == emr_id

    test.next_step()
    assert test.status == JobStatus.failed


def test_geotrellis_retries_big(monkeypatch):
    monkeypatch.setattr(GeotrellisJob, "check_analysis", lambda x: JobStatus.failed)
    monkeypatch.setattr(GeotrellisJob, "_get_emr_inputs", lambda x: {})

    test_big = GeotrellisJob(
        id="test2",
        status=JobStatus.starting,
        analysis_version="vtest",
        sync_version="vtestsync",
        table=AnalysisInputTable(
            dataset="test_dataset", version="vtestds", analysis=Analysis.glad
        ),
        features_1x1="s3://gfw-pipelines-test/test_zonal_stats/vtest1/vector/epsg-4326/test_zonal_stats_vtest1_1x1.tsv",
        geotrellis_version="1.3.0",
    )

    # too big, don't retry
    monkeypatch.setattr(GeotrellisJob, "_get_byte_size", lambda self, x: 10000000000)
    monkeypatch.setattr(GeotrellisJob, "_run_job_flow", lambda x: "j-big")

    test_big.next_step()
    assert test_big.status == JobStatus.executing
    assert test_big.step == GeotrellisJobStep.analyzing
    assert test_big.emr_job_id == "j-big"

    test_big.next_step()
    assert test_big.status == JobStatus.failed


def test_radd_sync(monkeypatch):
    mock_dp_config = DatapumpConfig(
        analysis_version="v20220101",
        dataset="wur_radd_alerts",
        dataset_version="v20220101",
        analysis="",
        sync=True,
        sync_type=SyncType.wur_radd_alerts,
    )

    monkeypatch.setattr(RADDAlertsSync, "get_latest_api_version", lambda x: "v20211018")
    monkeypatch.setattr(RADDAlertsSync, "get_latest_release", lambda x: "v20220222")

    radd_jobs = RADDAlertsSync("v20220101").build_jobs(mock_dp_config)

    assert radd_jobs
    job = radd_jobs[0]
    assert isinstance(job, RasterVersionUpdateJob)
    assert job.version == "v20220222"
    assert job.content_date_range.max == "2022-02-22"


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
            "s3://gfw-pipelines-test/geotrellis/results/vtestsync/test_dataset",
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
