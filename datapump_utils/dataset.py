import requests
import json

from datapump_utils.secrets import token
from datapump_utils.util import api_prefix
from datapump_utils.exceptions import UnexpectedResponseError


def get_dataset(dataset_id):
    url = f"https://{api_prefix()}-api.globalforestwatch.org/v1/dataset/{dataset_id}"
    response = requests.get(url)

    if response.status_code == 200:
        response_json = json.loads(response.text)
        attributes = response_json["data"]["attributes"]
        attributes["id"] = response_json["data"][
            "id"
        ]  # just merge id to make easier to use
        return attributes
    else:
        raise UnexpectedResponseError(
            f"Get dataset {dataset_id} returned status code {response.status_code}."
        )


def get_task(task_path):
    url = f"https://{api_prefix()}-api.globalforestwatch.org{task_path}"
    response = requests.get(url)

    if response.status_code == 200:
        response_json = json.loads(response.text)
        attributes = response_json["data"]["attributes"]
        attributes["id"] = response_json["data"][
            "id"
        ]  # just merge id to make easier to use
        return attributes
    elif response.status_code == 404:
        return None
    else:
        raise UnexpectedResponseError(
            f"Get task {task_path} returned status code {response.status_code}."
        )


def upload_dataset(dataset_id, source_urls, upload_type):
    url = f"https://{api_prefix()}-api.globalforestwatch.org/v1/dataset/{dataset_id}/{upload_type}"

    payload = _get_upload_dataset_payload(source_urls)
    r = requests.post(url, data=json.dumps(payload), headers=_get_headers())

    if r.status_code != 204:
        raise UnexpectedResponseError(
            f"Data upload failed with status code {r.status_code} and message: {r.json()}"
        )


def _get_upload_dataset_payload(source_urls):
    return {"provider": "csv", "sources": source_urls}


def delete_task(task_path):
    url = f"https://{api_prefix()}-api.globalforestwatch.org{task_path}"
    response = requests.delete(url, headers=_get_headers())

    if response.status_code != 200:
        raise UnexpectedResponseError(
            f"Delete task {task_path} returned status code {response.status_code}."
        )


def recover_dataset(dataset_id):
    """
    Resets dataset if stuck on a write.
    """
    url = f"https://{api_prefix()}-api.globalforestwatch.org/v1/dataset/{dataset_id}/recover"
    response = requests.post(url, headers=_get_headers())

    if response.status_code != 200:
        raise UnexpectedResponseError(
            f"Recover dataset {dataset_id} returned status code {response.status_code}."
        )


def create_dataset(dataset_id, source_urls):
    url = f"https://{api_prefix()}-api.globalforestwatch.org/v1/dataset"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token()}",
    }

    payload = {
        "provider": "tsv",
        "connectorType": "document",
        "application": ["gfw"],
        "name": dataset_id,
        "sources": source_urls,
    }

    r = requests.post(url, data=json.dumps(payload), headers=headers)

    if r.status_code != 204:
        raise Exception(
            "Data upload failed - received status code {}: "
            "Message: {}".format(r.status_code, r.json)
        )


def _get_headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token()}",
    }
