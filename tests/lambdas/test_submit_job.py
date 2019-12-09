import os
from unittest import mock

from geotrellis_summary_update.util import get_curr_date_dir_name, bucket_suffix

from lambdas.submit_job.src.lambda_function import handler

os.environ["ENV"] = "test"
os.environ[
    "GEOTRELLIS_JAR"
] = "s3://gfw-pipelines-dev/geotrellis/jars/treecoverloss-assembly-1.0.0-pre-e63f58ebf332741f9cde986a2f2e98f63ef8bda3.jar"
job_flow_id = "TESTID"


def test_handler():
    name = "new_area_test2"
    src = f"s3://gfw-pipelines-{bucket_suffix()}/geotrellis/features/*.tsv"
    feature_type = "geostore"
    result_dir = f"geotrellis/results/{name}/{get_curr_date_dir_name()}"
    upload_type = "data-overwrite"

    with mock.patch(
        "lambdas.submit_job.src.lambda_function.submit_summary_batch_job",
        return_value=job_flow_id,
    ):
        result = handler(
            {
                "name": name,
                "feature_src": src,
                "feature_type": feature_type,
                "upload_type": upload_type,
                "analyses": {
                    "gladalerts": {
                        "daily_alerts": "72af8802-df3c-42ab-a369-5e7f2b34ae2f",  # pragma: allowlist secret
                    }
                },
                "instance_size": "r4.2xlarge",
                "instance_count": 4,
                "dataset_ids": [],
            },
            None,
        )

    assert result["status"] == "SUCCESS"
    assert result["job_flow_id"] == job_flow_id
    assert result["name"] == name
    assert list(result["analyses"].keys()) == ["gladalerts"]
    assert result["feature_src"] == src
    assert result["feature_type"] == feature_type
    assert result["result_dir"] == result_dir
    assert result["upload_type"] == upload_type
