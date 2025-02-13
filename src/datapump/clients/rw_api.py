import csv
import io
import json
import urllib.request

import requests

from ..globals import GLOBALS, LOGGER
from ..util.exceptions import UnexpectedResponseError
from ..util.slack import slack_webhook
from ..util.util import api_prefix, get_date_string
from .aws import get_secrets_manager_client

TOKEN = None


def token() -> str:
    global TOKEN
    if TOKEN is None:
        TOKEN = _get_token()

    return TOKEN


def _get_token() -> str:
    response = get_secrets_manager_client().get_secret_value(
        SecretId=GLOBALS.token_secret_id
    )

    return json.loads(response["SecretString"])["token"]


def update_area_statuses(geostore_ids, status):
    url = f"https://{api_prefix()}-api.globalforestwatch.org/v2/area/update"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token()}",
    }

    errors = False
    LOGGER.info(f"Updating {len(geostore_ids)} geostore_ids to {status}")
    for gid in geostore_ids:
        r = requests.post(
            url,
            json=_update_aoi_statuses_payload([gid], status),
            headers=headers,
        )

        if r.status_code != 200:
            LOGGER.error(
                f"Status update failed for geostore {gid} with {r.status_code}"
            )

    if errors:
        slack_webhook(
            "WARNING", "Some user areas could not have statuses updated. See logs."
        )

    return 200


def _update_aoi_statuses_payload(geostore_ids, status):
    return {
        "geostores": geostore_ids,
        "update_params": {"status": status},
    }


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
        try:
            message = r.json()
        except ValueError:
            message = r.text

        raise UnexpectedResponseError(
            f"Data upload failed with status code {r.status_code} and message: {message}"
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
        "overwrite": True,
        "name": name,
        "sources": source_urls,
        "legend": legend,
    }

    LOGGER.info(f"Creating dataset at URI {url} with token {token()} body {payload}")
    r = requests.post(url, data=json.dumps(payload), headers=headers)

    if r.status_code == 200:
        return r.json()["data"]["id"]
    else:
        raise Exception(
            "Data upload failed - received status code {}: "
            "Message: {}".format(r.status_code, r.json())
        )


def _get_legend(source_url):
    src_url_open = urllib.request.urlopen(source_url)
    src_csv = csv.reader(
        io.TextIOWrapper(src_url_open, encoding="utf-8"), delimiter="\t"
    )
    header_row = next(src_csv)

    legend = dict()
    for col in header_row:
        # if in a whitelist table, just always use keyword because it's all true/false
        if "whitelist" in source_url:
            legend_type = "keyword"
        else:
            legend_type = get_legend_type(col)

        if legend_type in legend:
            legend[legend_type].append(col)
        elif legend_type == "lat" or legend_type == "long":
            legend[legend_type] = col
        else:
            legend[legend_type] = [col]

    return legend


def get_legend_type(field):
    if (
        field.endswith("__Mg")
        or field.endswith("__ha")
        or field.endswith("__K")
        or field.endswith("__MW")
    ):
        return "double"
    elif (
        field.endswith("__threshold")
        or field.endswith("__count")
        or field.endswith("__perc")
        or field.endswith("__year")
        or field.endswith("__week")
        or field == "adm1"
        or field == "adm2"
    ):
        return "integer"
    elif field == "latitude":
        return "lat"
    elif field == "longitude":
        return "long"
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
