import json

import boto3

from datapump_utils.util import secret_suffix

TOKEN = None


def token() -> str:
    global TOKEN
    if TOKEN is None:
        TOKEN = _get_token()

    return TOKEN


def _get_token() -> str:
    sm_client = boto3.client("secretsmanager")
    response = sm_client.get_secret_value(SecretId=f"gfw-api/token")

    return json.loads(response["SecretString"])["token"]
