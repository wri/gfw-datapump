import os
from typing import List, Optional, Sequence

import boto3
from google.cloud import storage

from ..globals import GLOBALS, LOGGER


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


def get_gs_files(
    bucket: str,
    prefix: str,
    limit: Optional[int] = None,
    exit_after_max: Optional[int] = None,
    extensions: Sequence[str] = tuple(),
) -> List[str]:
    """Get all matching files in GCS.
    Adapted from data API.
    """
    set_gcs_credentials()

    storage_client = storage.Client.from_service_account_json(
        GLOBALS.google_application_credentials
    )

    matches: List[str] = list()
    num_matches: int = 0

    blobs = list(storage_client.list_blobs(bucket, prefix=prefix, max_results=limit))

    LOGGER.info(f"Found files under gs://{bucket}/{prefix}: {blobs}")
    for blob in blobs:
        if not extensions or any(blob.name.endswith(ext) for ext in extensions):
            matches.append(blob.name)
            num_matches += 1
            if exit_after_max and num_matches >= exit_after_max:
                break

    return matches


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


def get_gs_file_as_text(
    bucket: str,
    key: str,
) -> str:
    """
    Get contents of a file as a string
    """
    set_gcs_credentials()

    storage_client = storage.Client.from_service_account_json(
        GLOBALS.google_application_credentials
    )

    blob = storage_client.get_bucket(bucket).get_blob(key)
    return blob.download_as_text(encoding="utf-8")
