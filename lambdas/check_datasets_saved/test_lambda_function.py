import os

from geotrellis_summary_update.util import secret_suffix

from .lambda_function import handler

os.environ["ENV"] = "test"

NAME = "new_area_test"
SRC = "s3://gfw-pipelines-dev/geotrellis/features/*.tsv"


def test_secret_suffix():
    assert secret_suffix() == "staging"


def test_e2e():
    result = handler(
        {
            "name": NAME,
            "feature_src": SRC,
            "analyses": {
                "gladalerts": {
                    "daily_alerts": "79014cd2-d5e2-4411-9160-a13b2b352c03",
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
