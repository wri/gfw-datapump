import boto3
import requests
import json

from geotrellis_summary_update.secrets import get_token
from geotrellis_summary_update.util import api_prefix


def get_dataset_status(dataset_id):
    print(api_prefix())
    url = f"https://{api_prefix()}-api.globalforestwatch.org/v1/dataset/{dataset_id}"
    response = requests.get(url)
    response_json = json.loads(response.text)
    print(response_json)
    return response_json["data"]["attributes"]["status"]


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
