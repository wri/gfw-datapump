import pytest
from moto import mock_secretsmanager
from requests_mock.exceptions import NoMockAddress

from geotrellis_summary_update.dataset import (
    upload_dataset,
    get_dataset,
    get_task,
    delete_task,
    recover_dataset,
    _get_headers,
    _get_upload_dataset_payload,
)
from geotrellis_summary_update.secrets import get_token
from geotrellis_summary_update.exceptions import UnexpectedResponseError
from tests.mock_environment.mock_environment import mock_environment
from tests.mock_environment.mock_responses import (
    TEST_DATASET_RESPONSE,
    TEST_ERROR_RESPONSE,
    TEST_TASK_RESPONSE,
)


@mock_secretsmanager
def test_get_token():
    mock_environment()

    token = get_token()
    assert token == "footoken"


@mock_secretsmanager
def test_get_headers():
    mock_environment()

    headers = _get_headers()
    assert headers == _mock_headers()


@mock_secretsmanager
def test_upload_dataset(requests_mock):
    mock_environment()
    requests_mock.post(
        "https://staging-api.globalforestwatch.org/v1/dataset/test_id/data-overwrite",
        status_code=204,
        headers=_mock_headers(),
    )

    source_urls = ["http://data/source/1.csv", "http://data/source/2.csv"]

    data_overwrite_payload = _get_upload_dataset_payload("data-overwrite", source_urls)
    assert data_overwrite_payload == {"provider": "csv", "data": source_urls}

    concat_payload = _get_upload_dataset_payload("concat", source_urls)
    assert concat_payload == {"provider": "csv", "sources": source_urls}

    try:
        upload_dataset("test_id", source_urls, "data-overwrite")
    except NoMockAddress:
        pytest.fail("POST request did not match URL or headers correctly.")

    requests_mock.post(
        "https://staging-api.globalforestwatch.org/v1/dataset/test_id/concat",
        status_code=400,
        headers=_mock_headers(),
        json=TEST_ERROR_RESPONSE,
    )

    with pytest.raises(UnexpectedResponseError):
        upload_dataset("test_id", source_urls, "concat")


def test_get_dataset(requests_mock):
    requests_mock.get(
        "https://staging-api.globalforestwatch.org/v1/dataset/foo_id",
        status_code=200,
        json=TEST_DATASET_RESPONSE,
    )

    ds = get_dataset("foo_id")
    assert ds["id"] == "foo_id"
    assert ds["sources"] == ["https://foo/data/source.csv"]
    assert ds["taskId"] == "/v1/doc-importer/task/foo_id"

    requests_mock.get(
        "https://staging-api.globalforestwatch.org/v1/dataset/foo_id",
        status_code=400,
        json=TEST_ERROR_RESPONSE,
    )

    with pytest.raises(UnexpectedResponseError):
        get_dataset("foo_id")


def test_get_task(requests_mock):
    url = "https://staging-api.globalforestwatch.org/v1/doc-importer/task/foo_id"
    requests_mock.get(url, status_code=200, json=TEST_TASK_RESPONSE)

    task_id = TEST_DATASET_RESPONSE["data"]["attributes"]["taskId"]
    task = get_task(task_id)

    assert task["id"] == "foo_id"
    assert task["reads"] == 1
    assert task["writes"] == 1

    requests_mock.get(url, status_code=404, json=TEST_ERROR_RESPONSE)
    task = get_task(task_id)
    assert task is None

    requests_mock.get(url, status_code=400, json=TEST_ERROR_RESPONSE)
    with pytest.raises(UnexpectedResponseError):
        get_task(task_id)


@mock_secretsmanager
def test_delete_task(requests_mock):
    mock_environment()

    url = "https://staging-api.globalforestwatch.org/v1/doc-importer/task/foo_id"
    task_id = TEST_DATASET_RESPONSE["data"]["attributes"]["taskId"]

    requests_mock.delete(url, status_code=200, headers=_mock_headers())
    try:
        delete_task(task_id)
    except NoMockAddress:
        pytest.fail()

    requests_mock.delete(url, status_code=400, headers=_mock_headers())
    with pytest.raises(UnexpectedResponseError):
        delete_task(task_id)


@mock_secretsmanager
def test_recover_dataset(requests_mock):
    mock_environment()

    url = "https://staging-api.globalforestwatch.org/v1/dataset/foo_id/recover"

    requests_mock.post(url, status_code=200, headers=_mock_headers())
    try:
        recover_dataset("foo_id")
    except NoMockAddress:
        pytest.fail()


def _mock_headers():
    return {
        "Content-Type": "application/json",
        "Authorization": "Bearer footoken",
    }
