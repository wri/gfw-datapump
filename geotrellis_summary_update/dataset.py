import boto3
import requests
import json
import logging

from geotrellis_summary_update.secrets import get_token
from geotrellis_summary_update.util import api_prefix
from geotrellis_summary_update.exceptions import UnexpectedResponseError


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
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_token()}",
    }

    src_param = "sources" if upload_type == "concat" else "data"
    payload = {"provider": "csv", src_param: source_urls}

    r = requests.post(url, data=json.dumps(payload), headers=headers)

    if r.status_code != 204:
        raise Exception(
            "Data upload failed - received status code {}: "
            "Message: {}".format(r.status_code, r.json())
        )


def get_api_token():
    client = boto3.client("secretsmanager", region_name="us-east-1")

    response = client.get_secret_value(SecretId=f"gfw-api/{get_token()}-token")
    return json.loads(response["SecretString"])["token"]


def create_dataset(dataset_id, source_urls):
    url = f"https://{api_prefix()}-api.globalforestwatch.org/v1/dataset"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_token()}",
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


def delete_task(task_path):
    url = f"https://{api_prefix()}-api.globalforestwatch.org{task_path}"
    response = requests.delete(url)

    if response.status_code != 200:
        raise UnexpectedResponseError(
            f"Delete task {task_path} returned status code {response.status_code}."
        )


def recover_dataset(dataset_id):
    """
    Resets dataset if stuck on a write.
    """
    url = f"https://{api_prefix()}-api.globalforestwatch.org/v1/dataset/{dataset_id}/recover"
    response = requests.post(url)

    if response.status_code != 200:
        raise UnexpectedResponseError(
            f"Recover dataset {dataset_id} returned status code {response.status_code}."
        )
