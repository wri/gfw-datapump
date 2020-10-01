from moto import mock_s3, mock_secretsmanager
from mock import patch
from datetime import datetime, timedelta
import pytz

from tests.mock_environment.mock_environment import mock_environment
from datapump_utils.util import bucket_suffix
from lambdas.check_new_glad_alerts.src.lambda_function import (
    check_for_new_glad_alerts_in_past_day,
    get_dataset_ids,
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
def test_get_dataset_ids():
    mock_environment()

    dataset_ids = get_dataset_ids("geostore")

    assert "annualupdate_minimal" not in dataset_ids
    assert "gladalerts" in dataset_ids
    assert "summary" not in dataset_ids["gladalerts"]
    assert "daily_alerts" in dataset_ids["gladalerts"]
    assert "weekly_alerts" in dataset_ids["gladalerts"]

    dataset_ids = get_dataset_ids("gadm")

    assert "annualupdate_minimal" not in dataset_ids
    assert "gladalerts" in dataset_ids

    assert "summary" not in dataset_ids["gladalerts"]["iso"]
    assert "summary" not in dataset_ids["gladalerts"]["adm1"]

    assert "weekly_alerts" in dataset_ids["gladalerts"]["iso"]
    assert "weekly_alerts" in dataset_ids["gladalerts"]["adm1"]


@mock_s3
@mock_secretsmanager
def test_handler_alerts_found():
    mock_environment()

    result = handler({}, None)
    geostore_result = result["geostore"]

    assert result["status"] == "NEW_ALERTS_FOUND"
    assert geostore_result["upload_type"] == "data-overwrite"
    assert geostore_result["get_summary"] is False
    assert geostore_result["analyses"] == ["gladalerts"]
    assert geostore_result["datasets"] == {
        "gladalerts": {
            "daily_alerts": ["testid_daily_alerts_glad"],
            "weekly_alerts": ["testid_weekly_alerts_glad"],
        },
    }
    assert (
        geostore_result["feature_src"]
        == f"s3://gfw-pipelines{bucket_suffix()}/geotrellis/features/geostore/*.tsv"
    )

    assert result["gadm"]["feature_type"] == "gadm"
    assert (
        result["gadm"]["feature_src"]
        == "s3://gfw-files/2018_update/tsv/gadm36_adm2_1_1.csv"
    )

    assert result["wdpa"]["feature_type"] == "wdpa"
    assert (
        result["wdpa"]["feature_src"]
        == "s3://gfw-data-lake/wdpa_protected_areas/v202007/vector/epsg-4326/wdpa_protected_areas_v202007_1x1.tsv"
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


@mock_s3
@mock_secretsmanager
@patch("lambdas.check_new_glad_alerts.src.lambda_function._now")
def test_handler_manual(mock_now):
    mock_environment()

    # mock datetime.now() as two days from now to make the mocked s3 tifs appear not updated recently
    mock_now.return_value = datetime.now(pytz.utc) + timedelta(days=2)

    result = handler({"manual": "true"}, None)
    assert result["status"] == "NEW_ALERTS_FOUND"
