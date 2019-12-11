import json

import boto3

from datapump_utils.util import secret_suffix


def get_token() -> str:
    sm_client = boto3.client("secretsmanager")
    response = sm_client.get_secret_value(SecretId=f"gfw-api/{secret_suffix()}-token")

    return json.loads(response["SecretString"])["token"]