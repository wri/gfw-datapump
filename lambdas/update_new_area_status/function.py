from upload_records.tasks import get_task_log
from upload_records.aws import get_api_token
from upload_records.errors import DatasetFailedError, DatasetPendingError
from summary_analysis_batch.utils import slack_webhook

import requests
import json
import boto3
import csv


def handler(event, context):
    name = event["name"]
    env = event["env"]
    analyses = event["analyses"]
    aoi_src = event["feature_src"]

    geostore_ids = get_aoi_geostore_ids(aoi_src, env)
    update_aoi_status(geostore_ids, env)


def get_aoi_geostore_ids(aoi_src, env="production"):
    s3_client = boto3.client("s3")

    tsv_list = s3_client.list_objects(Bucket=NEW_AOI_BUCKET, Prefix=NEW_AOI_PREFIX)['Contents']
    geostore_ids = []

    for object in tsv_list:
        tsv = s3_client.get_object(Bucket=NEW_AOI_BUCKET, Key=object["Key"])
        tsv_lines = tsv['Body'].read().decode('utf-8').split()
        for row in csv.DictReader(tsv_lines, delimiter="\t"):
            geostore_ids.append(row["geostore_id"])

    return geostore_ids


def update_aoi_status(geostore_ids, env="production"):
    url = "https://{}-api.globalforestwatch.org/v1/area".format(env)
    token = get_api_token(env)

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(token),
    }

    payload = {
        "application": "gfw",
        "geostore_ids": geostore_ids,
        "status": "complete"
    }

    r = requests.patch(url, data=json.dumps(payload), headers=headers)

    if r.status_code != 204:
        raise Exception(
            "Data upload failed - received status code {}: "
            "Message: {}".format(r.status_code, r.json)
        )
