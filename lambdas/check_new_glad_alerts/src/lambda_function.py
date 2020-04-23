from datetime import datetime, timedelta
from copy import deepcopy
import dateutil.tz as tz
import os
import json

from datapump_utils.s3 import s3_client, get_s3_path_parts

GLAD_STATUS_PATH = os.environ["GLAD_STATUS_PATH"]
DATASETS = json.loads(os.environ["DATASETS"])
S3_BUCKET_PIPELINE = os.environ["S3_BUCKET_PIPELINE"]


def handler(event, context):
    new_alerts = event.get("manual", check_for_new_glad_alerts_in_past_day())

    if new_alerts:
        return {
            "status": "NEW_ALERTS_FOUND",
            "geostore": {
                "instance_size": "r4.2xlarge",
                "instance_count": 30,
                "feature_src": f"s3://{S3_BUCKET_PIPELINE}/geotrellis/features/geostore/*.tsv",
                "feature_type": "geostore",
                "analyses": ["gladalerts"],
                "datasets": get_dataset_ids("geostore"),
                "name": "glad-alerts-geostore",
                "upload_type": "data-overwrite",
                "get_summary": False,
            },
            "gadm": {
                "instance_size": "r4.2xlarge",
                "instance_count": 30,
                "feature_src": "s3://gfw-files/2018_update/tsv/gadm36_adm2_1_1.csv",
                "feature_type": "gadm",
                "analyses": ["gladalerts"],
                "datasets": get_dataset_ids("gadm"),
                "name": "glad-alerts-gadm",
                "upload_type": "data-overwrite",
                "get_summary": False,
            },
            "wdpa": {
                "instance_size": "r4.2xlarge",
                "instance_count": 30,
                "feature_src": "s3://gfw-files/2018_update/tsv/wdpa_protected_areas_v201909_1_1.tsv",
                "feature_type": "wdpa",
                "analyses": ["gladalerts"],
                "datasets": get_dataset_ids("wdpa"),
                "name": "glad-alerts-wdpa",
                "upload_type": "data-overwrite",
                "get_summary": False,
            },
        }
    else:
        return {"status": "NO_NEW_ALERTS_FOUND"}


def check_for_new_glad_alerts_in_past_day():
    glad_alerts_bucket, glad_status = get_s3_path_parts(GLAD_STATUS_PATH)
    response = s3_client().get_object(Bucket=glad_alerts_bucket, Key=glad_status)

    last_modified_datetime = response["LastModified"]
    status = response["Body"].read().strip().decode("utf-8")
    one_day_ago = _now() - timedelta(hours=24)

    if status in ["COMPLETED", "SAVED", "HADOOP RUNNING", "HADOOP FAILED"]:
        if one_day_ago <= last_modified_datetime <= _now():
            return True

    return False


def get_dataset_ids(feature_type):
    dataset_ids = dict()

    feature_datasets = DATASETS[feature_type]
    dataset_ids["gladalerts"] = deepcopy(
        feature_datasets["gladalerts"]
    )  # only want to update glad alerts

    if "summary" in dataset_ids["gladalerts"]:
        del dataset_ids["gladalerts"]["summary"]  # don't need to update summary daily

    if "whitelist" in dataset_ids["gladalerts"]:
        del dataset_ids["gladalerts"]["whitelist"]  # whitelist is based on summary

    return dataset_ids


def _now():
    return datetime.now(tz.UTC)
