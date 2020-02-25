from copy import deepcopy
from mock import patch

from moto import mock_s3, mock_emr, mock_secretsmanager
import requests_mock

from tests.mock_environment.mock_environment import mock_environment
from tests.mock_environment.mock_responses import (
    TEST_DATASET_RESPONSE,
    TEST_TASK_RESPONSE,
)

import lambdas.submit_job.src.lambda_function as submit_job
import lambdas.upload_results_to_datasets.src.lambda_function as upload_results_to_datasets
import lambdas.check_datasets_saved.src.lambda_function as check_datasets_saved
from datapump_utils.util import get_date_string, bucket_suffix
from datapump_utils.summary_analysis import JobStatus, _instances


@mock_s3
@mock_emr
@mock_secretsmanager
def test_geotrellis_summary_update():
    mock_environment()

    input_params = {
        "name": NAME,
        "feature_src": FEATURE_SRC,
        "feature_type": FEATURE_TYPE,
        "analyses": ANALYSES,
        "instance_size": INSTANCE_SIZE,
        "instance_count": INSTANCE_COUNT,
        "upload_type": "concat",
        "datasets": DATASETS,
        "get_summary": True,
    }

    submit_job_output = _test_submit_job(input_params)
    upload_results_to_datasets_output = _test_upload_results_to_datasets_concat(
        submit_job_output
    )
    check_datasets_saved_output = _test_check_datasets_saved(
        upload_results_to_datasets_output
    )

    assert check_datasets_saved_output


@mock_s3
@mock_emr
@mock_secretsmanager
@patch("datapump_utils.dataset._get_legend")
def test_geotrellis_summary_create(mock_get_legend):
    mock_environment()
    mock_get_legend.return_value = {}

    input_params = {
        "name": NAME,
        "feature_src": FEATURE_SRC,
        "feature_type": FEATURE_TYPE,
        "analyses": ANALYSES,
        "instance_size": INSTANCE_SIZE,
        "instance_count": INSTANCE_COUNT,
        "upload_type": "create",
        "datasets": DATASETS_CREATE,
        "get_summary": True,
    }

    submit_job_output = _test_submit_job(input_params)
    upload_results_to_datasets_output = _test_upload_results_to_datasets_create(
        submit_job_output
    )
    check_datasets_saved_output = _test_check_datasets_saved_create(
        upload_results_to_datasets_output
    )

    assert check_datasets_saved_output


@patch("datapump_utils.summary_analysis._instances")
def _test_submit_job(input_params, mock_instances):
    # workaround for this bug with moto: https://github.com/spulec/moto/issues/1708
    instances = _instances(NAME, INSTANCE_SIZE, INSTANCE_SIZE, INSTANCE_COUNT)
    del instances["InstanceGroups"][0]["EbsConfiguration"]
    del instances["InstanceGroups"][1]["EbsConfiguration"]
    mock_instances.return_value = instances

    result = submit_job.handler(input_params, None)

    assert result["status"] == "SUCCESS"
    assert "j-" in result["job_flow_id"]
    assert result["name"] == NAME
    assert result["analyses"] == ANALYSES
    assert result["feature_src"] == FEATURE_SRC
    assert result["feature_type"] == FEATURE_TYPE
    assert result["result_dir"] == RESULT_DIR
    assert result["datasets"] == input_params["datasets"]

    return result


@patch("lambdas.upload_results_to_datasets.src.lambda_function.get_job_status")
def _test_upload_results_to_datasets_concat(input_params, mock_get_job_status):
    mock_get_job_status.return_value = JobStatus.SUCCESS

    with requests_mock.Mocker() as request_mocker:
        for dataset_id in DATASET_IDS.values():
            request_mocker.post(
                f"https://staging-api.globalforestwatch.org/v1/dataset/{dataset_id}/concat",
                status_code=204,
            )

        result = upload_results_to_datasets.handler(input_params, None)

    assert result["status"] == "SUCCESS"
    assert result["name"] == NAME
    assert result["analyses"] == ANALYSES
    assert result["feature_src"] == FEATURE_SRC
    assert list(result["dataset_ids"].values()) == list(DATASET_IDS.values())
    assert result["dataset_sources"] == DATASET_SOURCES

    return result


@patch("lambdas.upload_results_to_datasets.src.lambda_function.get_job_status")
def _test_upload_results_to_datasets_create(input_params, mock_get_job_status):
    mock_get_job_status.return_value = JobStatus.SUCCESS

    with requests_mock.Mocker() as request_mocker:
        datasets = list(DATASET_IDS.items())
        resp_body = deepcopy(TEST_DATASET_RESPONSE)
        resp_body["data"]["id"] = datasets[0][1]
        resp_body["data"]["attributes"]["name"] = datasets[0][0]

        request_mocker.post(
            f"https://staging-api.globalforestwatch.org/v1/dataset",
            status_code=200,
            json=resp_body,
            additional_matcher=(lambda rq: rq.json()["name"] == datasets[0][0]),
        )

        datasets = list(DATASET_IDS.items())
        resp_body = deepcopy(TEST_DATASET_RESPONSE)
        resp_body["data"]["id"] = datasets[1][1]
        resp_body["data"]["attributes"]["name"] = datasets[1][0]

        request_mocker.post(
            f"https://staging-api.globalforestwatch.org/v1/dataset",
            status_code=200,
            json=resp_body,
            additional_matcher=(lambda rq: rq.json()["name"] == datasets[1][0]),
        )

        datasets = list(DATASET_IDS.items())
        resp_body = deepcopy(TEST_DATASET_RESPONSE)
        resp_body["data"]["id"] = datasets[2][1]
        resp_body["data"]["attributes"]["name"] = datasets[2][0]

        request_mocker.post(
            f"https://staging-api.globalforestwatch.org/v1/dataset",
            status_code=200,
            json=resp_body,
            additional_matcher=(lambda rq: rq.json()["name"] == datasets[2][0]),
        )

        datasets = list(DATASET_IDS.items())
        resp_body = deepcopy(TEST_DATASET_RESPONSE)
        resp_body["data"]["id"] = datasets[3][1]
        resp_body["data"]["attributes"]["name"] = datasets[3][0]

        request_mocker.post(
            f"https://staging-api.globalforestwatch.org/v1/dataset",
            status_code=200,
            json=resp_body,
            additional_matcher=(lambda rq: rq.json()["name"] == datasets[3][0]),
        )

        datasets = list(DATASET_IDS.items())
        resp_body = deepcopy(TEST_DATASET_RESPONSE)
        resp_body["data"]["id"] = datasets[4][1]
        resp_body["data"]["attributes"]["name"] = datasets[4][0]

        request_mocker.post(
            f"https://staging-api.globalforestwatch.org/v1/dataset",
            status_code=200,
            json=resp_body,
            additional_matcher=(lambda rq: rq.json()["name"] == datasets[4][0]),
        )
        result = upload_results_to_datasets.handler(input_params, None)

    assert result["status"] == "SUCCESS"
    assert result["name"] == NAME
    assert result["analyses"] == ANALYSES
    assert result["feature_src"] == FEATURE_SRC
    assert result["dataset_ids"] == DATASET_IDS
    assert result["dataset_sources"] == DATASET_SOURCES

    return result


def _test_check_datasets_saved(input_params):
    with requests_mock.Mocker() as request_mocker:
        for dataset_id in DATASET_IDS.values():
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


def _test_check_datasets_saved_create(input_params):
    with requests_mock.Mocker() as request_mocker:
        for dataset_id in DATASET_IDS.values():
            ds_response = deepcopy(TEST_DATASET_RESPONSE)
            ds_response["data"]["id"] = dataset_id
            ds_response["data"]["attributes"][
                "taskId"
            ] = f"/v1/doc-importer/task/{dataset_id}_task"

            task_response = deepcopy(TEST_TASK_RESPONSE)
            task_response["data"]["id"] = f"{dataset_id}_task"

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

        result = check_datasets_saved.handler(input_params, None)

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
RESULT_DIR = f"geotrellis/results/test/{get_date_string()}"
DATASETS = {
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
DATASETS_CREATE = {
    "gladalerts": {
        "daily_alerts": "Daily Alerts GLAD",
        "weekly_alerts": "Weekly Alerts GLAD",
        "summary": "Summary GLAD",
    },
    "annualupdate_minimal": {"change": "Change TCL", "summary": "Summary TCL"},
}
DATASET_IDS = {
    "Daily Alerts GLAD": "testid_daily_alerts_glad",
    "Weekly Alerts GLAD": "testid_weekly_alerts_glad",
    "Summary GLAD": "testid_summary_glad",
    "Change TCL": "testid_change_tcl",
    "Summary TCL": "testid_summary_tcl",
}
DATASET_SOURCES = [
    [
        f"https://gfw-pipelines{bucket_suffix()}.s3.amazonaws.com/geotrellis/results/test/{get_date_string()}/gladalerts_20191119_1245/geostore/daily_alerts/results1.csv",
        f"https://gfw-pipelines{bucket_suffix()}.s3.amazonaws.com/geotrellis/results/test/{get_date_string()}/gladalerts_20191119_1245/geostore/daily_alerts/results2.csv",
    ],
    [
        f"https://gfw-pipelines{bucket_suffix()}.s3.amazonaws.com/geotrellis/results/test/{get_date_string()}/gladalerts_20191119_1245/geostore/weekly_alerts/results1.csv",
        f"https://gfw-pipelines{bucket_suffix()}.s3.amazonaws.com/geotrellis/results/test/{get_date_string()}/gladalerts_20191119_1245/geostore/weekly_alerts/results2.csv",
    ],
    [
        f"https://gfw-pipelines{bucket_suffix()}.s3.amazonaws.com/geotrellis/results/test/{get_date_string()}/gladalerts_20191119_1245/geostore/summary/results1.csv",
        f"https://gfw-pipelines{bucket_suffix()}.s3.amazonaws.com/geotrellis/results/test/{get_date_string()}/gladalerts_20191119_1245/geostore/summary/results2.csv",
    ],
    [
        f"https://gfw-pipelines{bucket_suffix()}.s3.amazonaws.com/geotrellis/results/test/{get_date_string()}/annualupdate_minimal_20191119_1245/geostore/change/results1.csv",
        f"https://gfw-pipelines{bucket_suffix()}.s3.amazonaws.com/geotrellis/results/test/{get_date_string()}/annualupdate_minimal_20191119_1245/geostore/change/results2.csv",
    ],
    [
        f"https://gfw-pipelines{bucket_suffix()}.s3.amazonaws.com/geotrellis/results/test/{get_date_string()}/annualupdate_minimal_20191119_1245/geostore/summary/results1.csv",
        f"https://gfw-pipelines{bucket_suffix()}.s3.amazonaws.com/geotrellis/results/test/{get_date_string()}/annualupdate_minimal_20191119_1245/geostore/summary/results2.csv",
    ],
]
