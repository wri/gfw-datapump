import os

import boto3

from ..globals import GLOBALS


def set_gcs_credentials():
    if os.path.exists(GLOBALS.google_application_credentials):
        return

    secrets_client = boto3.client(
        "secretsmanager",
        region_name=GLOBALS.aws_region,
        endpoint_url=GLOBALS.aws_endpoint_uri,
    )

    response = secrets_client.get_secret_value(SecretId=GLOBALS.gcs_key_secret_arn)

    os.makedirs(
        os.path.dirname(GLOBALS.google_application_credentials),
        exist_ok=True,
    )

    with open(GLOBALS.google_application_credentials, "w") as f:
        f.write(response["SecretString"])
