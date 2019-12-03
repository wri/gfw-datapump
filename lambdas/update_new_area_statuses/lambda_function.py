import io
import json
import os
from typing import Set

import boto3
import requests

from geotrellis_summary_update.exceptions import UnexpectedResponseError
from geotrellis_summary_update.util import api_prefix
from geotrellis_summary_update.s3 import get_s3_path_parts
from geotrellis_summary_update.secrets import get_token


if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"

TOKEN: str = get_token()


def handler(event, context):
    try:
        aoi_src = event["feature_src"]

        geostore_ids = get_aoi_geostore_ids(aoi_src)
        update_aoi_status(geostore_ids)

        return {"status": "SUCCESS"}  # TODO: Still need to work on the return values
    except Exception:
        return {"status": "FAILED"}


def get_aoi_geostore_ids(aoi_src: str) -> Set[str]:
    s3_client = boto3.client("s3")
    geostore_ids = set()
    aoi_bucket, aoi_key = get_s3_path_parts(aoi_src)

    with io.BytesIO() as data:
        s3_client.download_fileobj(aoi_bucket, aoi_key, data)

        rows = data.getvalue().decode("utf-8").split("\n")

    first = True
    for row in rows:
        geostore_id = row.split("\t")[0]
        if first:
            first = False
        elif geostore_id:
            geostore_ids.add(geostore_id)

    return geostore_ids


def update_aoi_status(geostore_ids: Set[str]) -> int:

    url = f"https://{api_prefix()}-api.globalforestwatch.org/v1/area"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}",
    }

    payload = {
        "application": "gfw",
        "geostore_ids": list(geostore_ids),
        "status": "saved",
    }

    r = requests.patch(url, data=json.dumps(payload), headers=headers)

    if r.status_code != 204:
        raise UnexpectedResponseError(
            "Data upload failed - received status code {}: "
            "Message: {}".format(r.status_code, r.json)
        )
    else:
        return r.status_code
