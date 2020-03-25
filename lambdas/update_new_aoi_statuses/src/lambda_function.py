import json
import os
import io
from typing import Set

import requests

from datapump_utils.exceptions import UnexpectedResponseError
from datapump_utils.util import api_prefix, error
from datapump_utils.secrets import token
from datapump_utils.s3 import s3_client, get_s3_path_parts


if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"

AOI_UPDATED_STATUS = "saved"


def handler(event, context):
    event = json.loads(
        event["Output"]
    )  # workaround because nested step functions serialize the output
    try:
        aoi_src = event["feature_src"]

        geostore_ids = get_aoi_geostore_ids(aoi_src)
        update_aoi_statuses(geostore_ids)

        return {"status": "SUCCESS"}
    except UnexpectedResponseError as e:
        return error(str(e))


def get_aoi_geostore_ids(aoi_src: str) -> Set[str]:
    geostore_ids = set()
    aoi_bucket, aoi_key = get_s3_path_parts(aoi_src)

    with io.BytesIO() as data:
        s3_client().download_fileobj(aoi_bucket, aoi_key, data)

        rows = data.getvalue().decode("utf-8").split("\n")

    first = True
    for row in rows:
        geostore_id = row.split("\t")[0]
        if first:
            first = False
        elif geostore_id:
            geostore_ids.add(geostore_id)

    return geostore_ids


def update_aoi_statuses(geostore_ids: Set[str]) -> int:
    url = f"https://{api_prefix()}-api.globalforestwatch.org/v2/area/update"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token()}",
    }

    id_list = list(geostore_ids)
    update_page_size = 500
    for i in range(0, len(id_list), update_page_size):
        r = requests.post(
            url,
            data=json.dumps(
                _update_aoi_statuses_payload(id_list[i : i + update_page_size])
            ),
            headers=headers,
        )

        if r.status_code != 200:
            raise UnexpectedResponseError(
                f"Data upload failed on upload block {i} - received status code {r.status_code}, message: {r.json()}"
            )

    return 200


def _update_aoi_statuses_payload(geostore_ids):
    return {
        "geostores": geostore_ids,
        "update_params": {"status": AOI_UPDATED_STATUS},
    }
