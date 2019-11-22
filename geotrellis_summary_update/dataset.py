import boto3
import requests
import json


def get_dataset_status(dataset_id, env):
    url = "https://{}-api.globalforestwatch.org/v1/dataset/{}".format(env, dataset_id)
    response = requests.get(url)
    response_json = json.loads(response.text)
    return response_json["data"]["attributes"]["status"]


def create_dataset(dataset_id, source_urls, env="production"):
    url = "https://{}-api.globalforestwatch.org/v1/dataset".format(env)
    token = get_api_token(env)

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(token),
    }

    payload = {
        "provider": "tsv",
        "connectorType": "document",
        "application": ["gfw"],
        "name": dataset_id,
        "sources": source_urls
    }

    r = requests.post(url, data=json.dumps(payload), headers=headers)

    if r.status_code != 204:
        raise Exception(
            "Data upload failed - received status code {}: "
            "Message: {}".format(r.status_code, r.json)
        )


def concat_dataset(dataset_id, source_urls, env="production"):
    url = "https://{}-api.globalforestwatch.org/v1/dataset/{}/concat".format(env, dataset_id)
    token = get_api_token(env)

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(token),
    }

    payload = {"provider": "csv", "sources": source_urls}

    r = requests.post(url, data=json.dumps(payload), headers=headers)

    if r.status_code != 204:
        raise Exception(
            "Data upload failed - received status code {}: "
            "Message: {}".format(r.status_code, r.json)
        )


def get_api_token(env):
    client = boto3.client("secretsmanager", region_name="us-east-1")

    if env == "production":
        env = "prod"
    else:
        env = "staging"

    response = client.get_secret_value(
        SecretId="gfw-api/{}-token".format(env)
    )
    return json.loads(response["SecretString"])["token"]