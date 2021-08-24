#############
## Test some specific code paths without having to test the entire step function
#############
import os

os.environ["S3_BUCKET_PIPELINE"] = "gfw-pipelines-test"
os.environ["S3_BUCKET_DATA_LAKE"] = "gfw-data-lake-test"
os.environ["GEOTRELLIS_JAR_PATH"] = "s3://gfw-pipelines-test/geotrellis/jars"

from datapump.commands.analysis import Analysis, AnalysisInputTable
from datapump.jobs.geotrellis import FireAlertsGeotrellisJob, JobStatus


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
