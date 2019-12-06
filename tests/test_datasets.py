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

from moto import mock_secretsmanager
from requests_mock.exceptions import NoMockAddress
import boto3
import json
import pytest


@mock_secretsmanager
def test_get_token():
    _mock_secrets()

    token = get_token()
    assert token == "footoken"


@mock_secretsmanager
def test_get_headers():
    _mock_secrets()

    headers = _get_headers()
    assert headers == _mock_headers()


@mock_secretsmanager
def test_upload_dataset(requests_mock):
    _mock_secrets()
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
    _mock_secrets()

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
    _mock_secrets()

    url = "https://staging-api.globalforestwatch.org/v1/dataset/foo_id/recover"

    requests_mock.post(url, status_code=200, headers=_mock_headers())
    try:
        recover_dataset("foo_id")
    except NoMockAddress:
        pytest.fail()


@mock_secretsmanager
def _mock_secrets():
    client = boto3.client("secretsmanager", region_name="us-east-1")
    client.create_secret(
        Name="gfw-api/staging-token",
        SecretString=json.dumps({"token": "footoken", "email": "foo@bar.org"}),
    )


def _mock_headers():
    return {
        "Content-Type": "application/json",
        "Authorization": "Bearer footoken",
    }


TEST_ERROR_RESPONSE = {"errors": [{"status": 400, "detail": "Test error"}]}

TEST_DATASET_RESPONSE = {
    "data": {
        "id": "foo_id",
        "type": "dataset",
        "attributes": {
            "name": "Carbon Flux Summary - IDN.13 - v20190611",
            "slug": "Carbon-Flux-Summary-IDN13-v20190611",
            "type": None,
            "subtitle": None,
            "application": ["gfw"],
            "dataPath": None,
            "attributesPath": None,
            "connectorType": "document",
            "provider": "json",
            "userId": "58750a56dfc643722bdd02ab",
            "connectorUrl": "https://foo/connector",
            "sources": ["https://foo/data/source.csv"],
            "tableName": "foo_table_name",
            "status": "saved",
            "published": True,
            "overwrite": True,
            "verified": False,
            "blockchain": {},
            "mainDateField": None,
            "env": "production",
            "geoInfo": False,
            "protected": False,
            "legend": {
                "date": [],
                "region": [],
                "country": [],
                "nested": ["year_data"],
                "integer": ["threshold"],
                "short": [],
                "byte": [],
                "double": [
                    "extent_2000",
                    "total_area",
                    "total_biomass",
                    "weighted_biomass_per_ha",
                    "gross_annual_removals_carbon",
                    "weighted_gross_annual_removals_carbon_ha",
                    "gross_cumul_removals_carbon",
                    "weighted_gross_cumul_removals_carbon_ha",
                    "net_flux_co2",
                    "weighted_net_flux_co2_ha",
                    "agc_emissions_year",
                    "weighted_agc_emissions_year",
                    "bgc_emissions_year",
                    "weighted_bgc_emissions_year",
                    "deadwood_carbon_emissions_year",
                    "weighted_deadwood_carbon_emissions_year",
                    "litter_carbon_emissions_year",
                    "weighted_litter_carbon_emissions_year",
                    "soil_carbon_emissions_year",
                    "weighted_soil_carbon_emissions_year",
                    "total_carbon_emissions_year",
                    "weighted_carbon_emissions_year",
                    "agc_2000",
                    "weighted_agc_2000",
                    "bgc_2000",
                    "weighted_bgc_2000",
                    "deadwood_carbon_2000",
                    "weighted_deadwood_carbon_2000",
                    "litter_carbon_2000",
                    "weighted_litter_carbon_2000",
                    "soil_2000_year",
                    "weighted_soil_carbon_2000",
                    "total_carbon_2000",
                    "weighted_carbon_2000",
                    "gross_emissions_co2",
                    "weighted_gross_emissions_co2",
                ],
                "float": [],
                "half_float": [],
                "scaled_float": [],
                "boolean": [],
                "binary": [],
                "text": [],
                "keyword": [
                    "iso",
                    "adm1",
                    "adm2",
                    "gain",
                    "mangroves",
                    "tcs",
                    "ecozone",
                    "land_right",
                    "wdpa",
                    "ifl",
                    "plantations",
                ],
            },
            "clonedHost": {},
            "errorMessage": "",
            "taskId": "/v1/doc-importer/task/foo_id",
            "createdAt": "2019-06-11T21:09:30.629Z",
            "updatedAt": "2019-06-11T21:27:51.311Z",
            "dataLastUpdated": None,
            "widgetRelevantProps": [],
            "layerRelevantProps": [],
        },
    }
}

TEST_TASK_RESPONSE = {
    "data": {
        "id": "foo_id",
        "type": "task",
        "attributes": {
            "type": "TASK_OVERWRITE",
            "message": {
                "id": "foo",
                "type": "TASK_OVERWRITE",
                "datasetId": "foo",
                "fileUrl": "https://foo",
                "provider": "json",
                "index": "foo",
            },
            "status": "SAVED",
            "reads": 1,
            "writes": 1,
            "createdAt": "2019-06-11T21:27:34.451Z",
            "updatedAt": "2019-06-11T21:27:51.271Z",
            "index": "foo",
            "datasetId": "foo",
            "logs": [
                {
                    "id": "foo1",
                    "type": "STATUS_INDEX_CREATED",
                    "taskId": "foo_id",
                    "index": "foo",
                },
                {"id": "foo2", "type": "STATUS_READ_DATA", "taskId": "foo_id"},
                {"id": "foo3", "type": "STATUS_READ_FILE", "taskId": "foo_id"},
                {
                    "id": "foo4",
                    "type": "STATUS_WRITTEN_DATA",
                    "taskId": "foo_id",
                    "withErrors": True,
                    "detail": '{"type":"illegal_argument_exception","reason":"mapper [plantations] of different type, current_type [text], merged_type [long]"}',
                    "index": "foo",
                },
                {
                    "id": "foo5",
                    "type": "STATUS_IMPORT_CONFIRMED",
                    "taskId": "foo_id",
                    "lastCheckedDate": "2019-06-11T21:27:47.017Z",
                },
                {
                    "id": "foo6",
                    "type": "STATUS_INDEX_DELETED",
                    "taskId": "foo_id",
                    "lastCheckedDate": "2019-06-11T21:27:49.255Z",
                },
            ],
        },
    }
}
