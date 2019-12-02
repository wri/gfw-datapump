import os
from unittest import mock

from geotrellis_summary_update.util import get_curr_date_dir_name, bucket_suffix

from . import lambda_function

os.environ["ENV"] = "test"
job_flow_id = "TESTID"


@mock.patch(
    "__main__.lambda_function.submit_summary_batch_job", return_value=job_flow_id
)
def test_handler():
    name = "new_area_test2"
    src = f"s3://gfw-pipelines-{bucket_suffix()}/geotrellis/features/*.tsv"
    feature_type = "geostore"
    result_bucket = f"gfw-pipelines-{bucket_suffix()}"
    result_dir = f"geotrellis/results/{name}/{get_curr_date_dir_name()}"
    upload_type = "data-overwrite"

    result = lambda_function.handler(
        {
            "name": name,
            "feature_src": src,
            "feature_type": feature_type,
            "upload_type": upload_type,
            "analyses": {
                "gladalerts": {
                    "daily_alerts": "72af8802-df3c-42ab-a369-5e7f2b34ae2f",
                }  # flake8 --ignore
            },
        },
        None,
    )

    assert result["status"] == "SUCCESS"
    assert result["job_flow_id"] == job_flow_id
    assert result["name"] == name
    assert list(result["analyses"].keys()) == ["gladalerts"]
    assert result["feature_src"] == src
    assert result["feature_type"] == feature_type
    assert result["result_bucket"] == result_bucket
    assert result["result_dir"] == result_dir
    assert result["upload_type"] == upload_type
