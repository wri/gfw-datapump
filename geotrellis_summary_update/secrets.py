import boto3

from geotrellis_summary_update.util import secret_suffix


def get_token() -> str:
    sm_client = boto3.client("secretsmanager")
    return sm_client.get_secret_value(SecretId=f"gfw-api/{secret_suffix()}-token")
