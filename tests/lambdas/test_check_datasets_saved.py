import os

from geotrellis_summary_update.util import secret_suffix
from lambdas.check_datasets_saved.src.lambda_function import is_dataset_stuck_on_write

os.environ["ENV"] = "test"

NAME = "new_area_test"
SRC = "s3://gfw-pipelines-dev/geotrellis/features/*.tsv"


def test_is_dataset_stuck_on_write():
    ds_pending = {"status": "pending"}
    ds_saved = {"status": "saved"}

    task_correct = {"reads": 10, "writes": 10}
    task_too_few_reads = {"reads": 9, "writes": 10}

    assert not is_dataset_stuck_on_write(ds_pending, task_correct)
    assert is_dataset_stuck_on_write(ds_pending, task_too_few_reads)

    assert is_dataset_stuck_on_write(ds_saved, None)
    assert not is_dataset_stuck_on_write(ds_saved, task_correct)


def test_secret_suffix():
    assert secret_suffix() == "staging"


""""
def test_e2e():
    result = handler(
        {
            "name": NAME,
            "feature_src": SRC,
            "analyses": {
                "gladalerts": {
                    "daily_alerts": "79014cd2-d5e2-4411-9160-a13b2b352c03",  # pragma: allowlist secret
                    # "weekly_alerts": "Glad Alerts - Weekly - Geostore - User Areas",
                    # "summary": "Glad Alerts - Summary - Geostore - User Areas",
                }
            },
        },
        None,
    )

    assert result["status"] == "SUCCESS"
    assert result["name"] == NAME
    assert result["feature_src"] == SRC
    assert list(result["analyses"].keys()) == ["gladalerts"]
"""
