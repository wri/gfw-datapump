#############
## Test some specific code paths without having to test the entire step function
#############
from pathlib import Path
# from mock import patch

import os

os.environ["S3_BUCKET_PIPELINE"] = "gfw-pipelines-test"
os.environ["S3_BUCKET_DATA_LAKE"] = "gfw-data-lake-test"

from datapump.commands import Analysis, AnalysisInputTable
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


# @patch('datapump.jobs.geotrellis.GeotrellisJob._get_table_schema')
# def test_get_all_result_table(mocked_schema):
#     mocked_schema.return_value = []
#     job = FireAlertsGeotrellisJob(
#         id="test",
#         status=JobStatus.starting,
#         analysis_version="vtest",
#         sync_version="vtestsync",
#         table=AnalysisInputTable(
#             dataset="test_dataset", version="vtestds", analysis=Analysis.viirs
#         ),
#         features_1x1="s3://gfw-pipelines-test/test_zonal_stats/vtest1/vector/epsg-4326/test_zonal_stats_vtest1_1x1.tsv",
#         geotrellis_version="1.3.0",
#         alert_type="viirs",
#         alert_sources=[
#             "s3://gfw-data-lake-test/viirs/test1.tsv",
#             "s3://gfw-data-lake-test/viirs/test2.tsv",
#         ],
#     )
#
#     mock_source_keys = [
#         "geotrells/results/rw_areas/viirs/gadm/all/1.tsv",
#         "geotrells/results/rw_areas/viirs/gadm/all/2.tsv",
#         "geotrells/results/rw_areas/viirs/gadm/all/3.tsv",
#     ]
#
#     result_table = job._get_result_table("gfw-pipelines-test", Path("geotrells/results/rw_areas/viirs/gadm/all"), mock_source_keys)
#     from pprint import pprint
#     pprint(result_table.dict())
#     assert result_table


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
            "s3://gfw-pipelines-dev/geotrellis/jars/treecoverloss-assembly-1.3.0.jar",
            "--output",
            "s3://gfw-pipelines-dev/geotrellis/results/vtestsync/test_dataset",
            "--features",
            "s3://gfw-pipelines-test/test_zonal_stats/vtest1/vector/epsg-4326/test_zonal_stats_vtest1_1x1.tsv",
            "--feature_type",
            "feature",
            "--analysis",
            "firealerts",
            "--fire_alert_type",
            "viirs",
            "--fire_alert_source",
            "s3://gfw-data-lake-test/viirs/test1.tsv",
            "--fire_alert_source",
            "s3://gfw-data-lake-test/viirs/test2.tsv",
        ],
    },
}
