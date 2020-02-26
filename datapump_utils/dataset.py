import requests
import json
import urllib.request
import csv
import io

from datapump_utils.secrets import token
from datapump_utils.util import api_prefix, get_date_string
from datapump_utils.exceptions import UnexpectedResponseError
from datapump_utils.logger import get_logger

LOGGER = get_logger(__name__)


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


def upload_dataset(dataset, source_urls, upload_type):
    if upload_type == "create":
        return create_dataset(dataset, source_urls)
    elif (
        upload_type == "concat"
        or upload_type == "data-overwrite"
        or upload_type == "append"
    ):
        return update_dataset(dataset, source_urls, upload_type)
    else:
        raise ValueError(f"Unknown upload type: {upload_type}")


def update_dataset(dataset_id, source_urls, upload_type):
    url = f"https://{api_prefix()}-api.globalforestwatch.org/v1/dataset/{dataset_id}/{upload_type}"

    payload = _get_upload_dataset_payload(source_urls)

    # data overwrite needs legend parameter since we're overwriting whole schema
    if upload_type == "data-overwrite":
        payload["legend"] = _get_legend(source_urls[0])

    LOGGER.info(f"Updating at URI {url} with body {payload}")
    r = requests.post(url, data=json.dumps(payload), headers=_get_headers())

    if r.status_code != 204:
        raise UnexpectedResponseError(
            f"Data upload failed with status code {r.status_code} and message: {r.json()}"
        )

    return dataset_id


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


def create_dataset(name, source_urls):
    url = f"https://{api_prefix()}-api.globalforestwatch.org/v1/dataset"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token()}",
    }

    legend = _get_legend(source_urls[0])
    payload = {
        "provider": "tsv",
        "connectorType": "document",
        "application": ["gfw"],
        "name": name,
        "sources": source_urls,
        "legend": legend,
    }

    LOGGER.info(f"Creating dataset at URI {url} with body {payload}")
    r = requests.post(url, data=json.dumps(payload), headers=headers)

    if r.status_code == 200:
        return r.json()["data"]["id"]
    else:
        raise Exception(
            "Data upload failed - received status code {}: "
            "Message: {}".format(r.status_code, r.json)
        )


def _get_legend(source_url):
    src_url_open = urllib.request.urlopen(source_url)
    src_csv = csv.reader(
        io.TextIOWrapper(src_url_open, encoding="utf-8"), delimiter="\t"
    )
    header_row = next(src_csv)

    legend = dict()
    for col in header_row:
        legend_type = get_legend_type(col)
        if legend_type in legend:
            legend[legend_type].append(col)
        else:
            legend[legend_type] = [col]

    return legend


def get_legend_type(field):
    if field.endswith("__Mg") or field.endswith("__ha"):
        return "double"
    elif (
        field.endswith("__threshold")
        or field.endswith("__count")
        or field == "treecover_loss__year"
    ):
        return "integer"
    else:
        return "keyword"


def _get_headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token()}",
    }


def _get_upload_dataset_payload(source_urls):
    return {"provider": "tsv", "sources": source_urls}


def _get_versioned_dataset_name(name):
    return f"{name} - v{get_date_string()}"
