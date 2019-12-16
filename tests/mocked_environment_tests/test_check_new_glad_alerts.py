from moto import mock_s3, mock_secretsmanager
from mock import patch
from datetime import datetime, timedelta
import pytz

from tests.mock_environment.mock_environment import mock_environment
from datapump_utils.util import bucket_suffix
from lambdas.check_new_glad_alerts.src.lambda_function import (
    check_for_new_glad_alerts_in_past_day,
    get_daily_glad_dataset_ids,
    handler,
)


@mock_s3
@mock_secretsmanager
def test_check_for_new_glad_alerts_in_past_day():
    mock_environment()

    assert check_for_new_glad_alerts_in_past_day()


@mock_s3
@mock_secretsmanager
@patch("lambdas.check_new_glad_alerts.src.lambda_function._now")
def test_no_new_glad_alerts_in_past_day(mock_now):
    mock_environment()

    # mock datetime.now() as two days from now to make the mocked s3 tifs appear not updated recently
    mock_now.return_value = datetime.now(pytz.utc) + timedelta(days=2)

    assert not check_for_new_glad_alerts_in_past_day()


@mock_s3
@mock_secretsmanager
def test_get_daily_glad_dataset_ids():
    mock_environment()

    dataset_ids = get_daily_glad_dataset_ids()

    assert "annualupdate_minimal" not in dataset_ids
    assert "gladalerts" in dataset_ids
    assert "summary" not in dataset_ids["gladalerts"]
    assert "daily_alerts" in dataset_ids["gladalerts"]
    assert "weekly_alerts" in dataset_ids["gladalerts"]


@mock_s3
@mock_secretsmanager
def test_handler_alerts_found():
    mock_environment()

    result = handler({}, None)

    assert result["status"] == "NEW_ALERTS_FOUND"
    assert result["upload_type"] == "data-overwrite"
    assert result["get_summary"] is False
    assert result["analyses"] == ["gladalerts"]
    assert result["datasets"] == {
        "gladalerts": {
            "daily_alerts": "testid_daily_alerts_glad",
            "weekly_alerts": "testid_weekly_alerts_glad",
        },
    }
    assert (
        result["feature_src"]
        == f"s3://gfw-pipelines{bucket_suffix()}/geotrellis/features/geostore/*.tsv"
    )


@mock_s3
@mock_secretsmanager
@patch("lambdas.check_new_glad_alerts.src.lambda_function._now")
def test_handler_no_alerts_found(mock_now):
    mock_environment()

    # mock datetime.now() as two days from now to make the mocked s3 tifs appear not updated recently
    mock_now.return_value = datetime.now(pytz.utc) + timedelta(days=2)

    result = handler({}, None)

    assert result["status"] == "NO_NEW_ALERTS_FOUND"
