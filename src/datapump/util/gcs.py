import os
from typing import List

import boto3
from google.cloud import storage

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


def get_gs_subfolders(
    bucket: str,
    prefix: str,
) -> List[str]:
    set_gcs_credentials()

    storage_client = storage.Client.from_service_account_json(
        GLOBALS.google_application_credentials
    )

    delimiter = "/"
    if not prefix.endswith(delimiter):
        prefix = prefix + delimiter

    blobs = storage_client.list_blobs(bucket, prefix=prefix, delimiter=delimiter)

    try:
        _ = next(blobs)
    except StopIteration:
        pass

    found_prefixes = [
        found_prefix.lstrip(prefix).strip("/") for found_prefix in blobs.prefixes
    ]

    return found_prefixes
