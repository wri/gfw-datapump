from geotrellis_summary_update.s3 import get_s3_path_parts
from geotrellis_summary_update.secrets import get_token
from typing import List

import requests
import json
import boto3
import csv

TOKEN: str = get_token()


def handler(event, context):
    env = event["env"]
    aoi_src = event["feature_src"]

    geostore_ids = get_aoi_geostore_ids(aoi_src, env)
    update_aoi_status(geostore_ids, env)


def get_aoi_geostore_ids(aoi_src: str, env="production") -> List[str]:
    s3_client = boto3.client("s3")
    geostore_ids = []
    aoi_bucket, aoi_key = get_s3_path_parts(aoi_src)

    tsv = s3_client.get_object(Bucket=aoi_bucket, Key=aoi_key)
    tsv_lines = tsv["Body"].read().decode("utf-8").split()
    for row in csv.DictReader(tsv_lines, delimiter="\t"):
        geostore_ids.append(row["geostore_id"])

    return geostore_ids


def update_aoi_status(geostore_ids: List[str], env="production") -> None:
    url = "https://{}-api.globalforestwatch.org/v1/area".format(env)

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(TOKEN),
    }

    payload = {"application": "gfw", "geostore_ids": geostore_ids, "status": "saved"}

    r = requests.patch(url, data=json.dumps(payload), headers=headers)

    if r.status_code != 204:
        raise Exception(
            "Data upload failed - received status code {}: "
            "Message: {}".format(r.status_code, r.json)
        )
