import json
import os
import io
from typing import Set

from datapump.util.exceptions import UnexpectedResponseError
from datapump.util import error
from datapump.util.s3 import s3_client, get_s3_path_parts
from datapump.util.logger import get_logger
from datapump.rw_api import update_area_statuses


if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"

AOI_UPDATED_STATUS = "saved"
LOGGER = get_logger(__name__)


def handler(event, context):
    event = json.loads(
        event["Output"]
    )  # workaround because nested step functions serialize the output
    try:
        aoi_src = event["feature_src"]

        geostore_ids = get_aoi_geostore_ids(aoi_src)
        update_area_statuses(geostore_ids, "saved")

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
