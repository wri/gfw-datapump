import lambdas.submit_job.lambda_function as submit_job
import lambdas.upload_results_to_datasets.lambda_function as upload_results_to_datasets
import lambdas.check_datasets_saved.lambda_function as check_datasets_saved

from geotrellis_summary_update.util import get_curr_date_dir_name
from geotrellis_summary_update.summary_analysis import JobStatus

from moto import mock_s3, mock_emr
from mock import patch
import requests_mock

from tests.mock_environment.mock_environment import _mock_s3_setup
from tests.mock_environment.mock_responses import (
    TEST_DATASET_RESPONSE,
    TEST_TASK_RESPONSE,
)
from copy import deepcopy


@mock_s3
@mock_emr
def test_geotrellis_summary_update():
    _mock_s3_setup()

    input_params = {
        "name": NAME,
        "feature_src": FEATURE_SRC,
        "feature_type": FEATURE_TYPE,
        "analyses": ANALYSES,
        "instance_size": INSTANCE_SIZE,
        "instance_count": INSTANCE_COUNT,
        "upload_type": UPLOAD_TYPE,
        "dataset_ids": DATASET_IDS,
    }

    submit_job_output = _test_submit_job(input_params)
    upload_results_to_datasets_output = _test_upload_results_to_datasets(
        submit_job_output
    )
    check_datasets_saved_output = _test_check_datasets_saved(
        upload_results_to_datasets_output
    )

    assert check_datasets_saved_output


def _test_submit_job(input_params):
    result = submit_job.handler(input_params, None)

    assert result["status"] == "SUCCESS"
    assert "j-" in result["job_flow_id"]
    assert result["name"] == NAME
    assert result["analyses"] == ANALYSES
    assert result["feature_src"] == FEATURE_SRC
    assert result["feature_type"] == FEATURE_TYPE
    assert result["result_dir"] == RESULT_DIR
    assert result["upload_type"] == UPLOAD_TYPE
    assert result["dataset_ids"] == DATASET_IDS

    return result


@patch("lambdas.upload_results_to_datasets.lambda_function.get_job_status")
def _test_upload_results_to_datasets(input_params, mock_get_job_status):
    mock_get_job_status.return_value = JobStatus.SUCCESS

    with requests_mock.Mocker() as request_mocker:
        for dataset_id in DATASET_IDS_FLAT:
            request_mocker.post(
                f"https://staging-api.globalforestwatch.org/v1/dataset/{dataset_id}/concat",
                status_code=204,
            )

        result = upload_results_to_datasets.handler(input_params, None)

    assert result["status"] == "SUCCESS"
    assert result["name"] == NAME
    assert result["analyses"] == ANALYSES
    assert result["feature_src"] == FEATURE_SRC
    assert result["upload_type"] == UPLOAD_TYPE
    assert result["dataset_ids"] == DATASET_IDS_FLAT
    assert result["dataset_sources"] == DATASET_SOURCES

    return result


def _test_check_datasets_saved(input_params):
    with requests_mock.Mocker() as request_mocker:
        for dataset_id in DATASET_IDS_FLAT:
            ds_response = deepcopy(TEST_DATASET_RESPONSE)
            ds_response["data"]["id"] = dataset_id
            ds_response["data"]["attributes"][
                "taskId"
            ] = f"/v1/doc-importer/task/{dataset_id}_task"

            task_response = deepcopy(TEST_TASK_RESPONSE)
            task_response["data"]["id"] = f"{dataset_id}_task"

            if dataset_id == "testid_change_tcl":
                task_response["data"]["attributes"]["reads"] = 5
                task_response["data"]["attributes"]["writes"] = 6
                ds_response["data"]["attributes"]["status"] = "pending"

                task_response["data"]["attributes"]["writes"]
                task_response["data"]["attributes"]["status"] = "pending"

                retry_ds_response = ds_response
                retry_task_response = task_response

            request_mocker.get(
                f"https://staging-api.globalforestwatch.org/v1/dataset/{dataset_id}",
                status_code=200,
                json=ds_response,
            )

            request_mocker.get(
                f"https://staging-api.globalforestwatch.org/v1/doc-importer/task/{dataset_id}_task",
                status_code=200,
                json=task_response,
            )

        request_mocker.delete(
            f"https://staging-api.globalforestwatch.org/v1/doc-importer/task/testid_change_tcl_task",
            status_code=200,
        )

        request_mocker.post(
            f"https://staging-api.globalforestwatch.org/v1/dataset/testid_change_tcl/recover",
            status_code=200,
        )

        request_mocker.post(
            f"https://staging-api.globalforestwatch.org/v1/dataset/testid_change_tcl/concat",
            status_code=204,
        )

        result_attempt_1 = check_datasets_saved.handler(input_params, None)

        assert result_attempt_1["status"] == "PENDING"
        assert result_attempt_1["retries"]["testid_change_tcl"] == 1

        retry_ds_response["data"]["attributes"]["status"] = "saved"
        retry_task_response["data"]["attributes"]["status"] = "SAVED"
        retry_task_response["data"]["attributes"]["writes"] = 5

        request_mocker.get(
            f"https://staging-api.globalforestwatch.org/v1/dataset/testid_change_tcl",
            status_code=200,
            json=retry_ds_response,
        )
        request_mocker.get(
            f"https://staging-api.globalforestwatch.org/v1/doc-importer/task/testid_change_tcl_task",
            status_code=200,
            json=retry_task_response,
        )

        result = check_datasets_saved.handler(result_attempt_1, None)

    assert result["status"] == "SUCCESS"
    assert result["name"] == NAME
    assert result["feature_src"] == FEATURE_SRC

    return result


NAME = "test"
FEATURE_SRC = "s3://test/src.tsv"
FEATURE_TYPE = "geostore"
ANALYSES = ["gladalerts", "annualupdate_minimal"]
INSTANCE_SIZE = "r4.xlarge"
INSTANCE_COUNT = 10
UPLOAD_TYPE = "concat"
RESULT_DIR = f"geotrellis/results/test/{get_curr_date_dir_name()}"
DATASET_IDS = {
    "gladalerts": {
        "daily_alerts": "testid_daily_alerts_glad",
        "weekly_alerts": "testid_weekly_alerts_glad",
        "summary": "testid_summary_glad",
    },
    "annualupdate_minimal": {
        "change": "testid_change_tcl",
        "summary": "testid_summary_tcl",
    },
}
DATASET_IDS_FLAT = [
    "testid_daily_alerts_glad",
    "testid_weekly_alerts_glad",
    "testid_summary_glad",
    "testid_change_tcl",
    "testid_summary_tcl",
]
DATASET_SOURCES = [
    [
        f"https://gfw-pipelines-dev.s3.amazonaws.com/geotrellis/results/test/{get_curr_date_dir_name()}/gladalerts_20191119_1245/geostore/daily_alerts/results1.csv",
        f"https://gfw-pipelines-dev.s3.amazonaws.com/geotrellis/results/test/{get_curr_date_dir_name()}/gladalerts_20191119_1245/geostore/daily_alerts/results2.csv",
    ],
    [
        f"https://gfw-pipelines-dev.s3.amazonaws.com/geotrellis/results/test/{get_curr_date_dir_name()}/gladalerts_20191119_1245/geostore/weekly_alerts/results1.csv",
        f"https://gfw-pipelines-dev.s3.amazonaws.com/geotrellis/results/test/{get_curr_date_dir_name()}/gladalerts_20191119_1245/geostore/weekly_alerts/results2.csv",
    ],
    [
        f"https://gfw-pipelines-dev.s3.amazonaws.com/geotrellis/results/test/{get_curr_date_dir_name()}/gladalerts_20191119_1245/geostore/summary/results1.csv",
        f"https://gfw-pipelines-dev.s3.amazonaws.com/geotrellis/results/test/{get_curr_date_dir_name()}/gladalerts_20191119_1245/geostore/summary/results2.csv",
    ],
    [
        f"https://gfw-pipelines-dev.s3.amazonaws.com/geotrellis/results/test/{get_curr_date_dir_name()}/annualupdate_minimal_20191119_1245/geostore/change/results1.csv",
        f"https://gfw-pipelines-dev.s3.amazonaws.com/geotrellis/results/test/{get_curr_date_dir_name()}/annualupdate_minimal_20191119_1245/geostore/change/results2.csv",
    ],
    [
        f"https://gfw-pipelines-dev.s3.amazonaws.com/geotrellis/results/test/{get_curr_date_dir_name()}/annualupdate_minimal_20191119_1245/geostore/summary/results1.csv",
        f"https://gfw-pipelines-dev.s3.amazonaws.com/geotrellis/results/test/{get_curr_date_dir_name()}/annualupdate_minimal_20191119_1245/geostore/summary/results2.csv",
    ],
]
