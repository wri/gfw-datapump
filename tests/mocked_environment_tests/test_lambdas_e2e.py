from moto import mock_s3, mock_emr, mock_secretsmanager
from tests.mock_environment.mock_environment import mock_environment

from lambdas.upload_results_to_datasets.src.lambda_function import handler
from datapump_utils.util import get_date_string

import requests_mock
from mock import patch


@mock_s3
@mock_emr
@mock_secretsmanager
def test_upload_results(requests_mock):
    mock_environment()

    adapter_change = requests_mock.post(
        "https://staging-api.globalforestwatch.org/v1/dataset/testid_change_tcl/append",
        status_code=204,
    )
    adapter_summary = requests_mock.post(
        "https://staging-api.globalforestwatch.org/v1/dataset/testid_summary_tcl/append",
        status_code=204,
    )

    output = handler(
        {
            "name": "test-update",
            "upload_type": "append",
            "output_url": f"s3://gfw-pipelines-dev/geotrellis/results/test_append/{get_date_string()}",
        },
        None,
    )

    assert adapter_change.call_count == 1
    assert adapter_summary.call_count == 1

    request_change = adapter_change.last_request.json()
    request_summary = adapter_summary.last_request.json()

    assert len(request_change["sources"]) == 2
    assert len(request_summary["sources"]) == 2

    assert output["dataset_ids"] == ["testid_change_tcl", "testid_summary_tcl"]
    assert (
        output["dataset_result_paths"]["testid_change_tcl"]
        == "s3://gfw-pipelines-dev/geotrellis/results/test_append/2020-05-12/annualupdate_minimal/geostore/change"
    )


@mock_s3
@mock_emr
@mock_secretsmanager
@patch("datapump_utils.dataset.dataset._get_legend")
def test_create_dataset(mock_get_legend, requests_mock):
    mock_environment()
    mock_get_legend.return_value = {}

    adapter_change = requests_mock.post(
        "https://staging-api.globalforestwatch.org/v1/dataset",
        status_code=200,
        json={"data": {"id": "testid_change_tcl"}},
    )

    output = handler(
        {
            "name": "test-update",
            "upload_type": "create",
            "version": "v20TEST",
            "tcl_year": 2019,
            "output_url": f"s3://gfw-pipelines-dev/geotrellis/results/test_create/{get_date_string()}",
        },
        None,
    )

    assert adapter_change.call_count == 1

    request_change = adapter_change.last_request.json()

    assert len(request_change["sources"]) == 2

    assert request_change["name"] == "Tree Cover Loss 2019 Change - Geostore - v20TEST"

    assert output["dataset_ids"] == ["testid_change_tcl"]
    assert (
        output["dataset_result_paths"]["testid_change_tcl"]
        == "s3://gfw-pipelines-dev/geotrellis/results/test_create/2020-05-12/annualupdate_minimal/geostore/change"
    )
