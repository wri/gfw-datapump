from datetime import datetime, timedelta
from copy import deepcopy
import dateutil.tz as tz
import os
import json

from datapump_utils.s3 import s3_client, get_s3_path_parts
from datapump_utils.util import bucket_suffix

NAME = "glad-alerts-aoi"
GLAD_ALERTS_PATH = os.environ["GLAD_ALERTS_PATH"]
AOI_DATASETS = json.loads(os.environ["AOI_DATASETS"])
S3_BUCKET_PIPELINE = os.environ["S3_BUCKET_PIPELINE"]


def handler(event, context):
    new_alerts = check_for_new_glad_alerts_in_past_day()
    if new_alerts:
        return {
            "status": "NEW_ALERTS_FOUND",
            "instance_size": "r4.2xlarge",
            "instance_count": 6,
            "feature_src": f"s3://{S3_BUCKET_PIPELINE}/geotrellis/features/geostore/*.tsv",
            "feature_type": "geostore",
            "analyses": ["gladalerts"],
            "datasets": get_daily_glad_dataset_ids(),
            "name": NAME,
            "upload_type": "data-overwrite",
            "get_summary": False,
        }
    else:
        return {"status": "NO_NEW_ALERTS_FOUND"}


def check_for_new_glad_alerts_in_past_day():
    glad_alerts_bucket, glad_alerts_prefix = get_s3_path_parts(GLAD_ALERTS_PATH)
    response = s3_client().list_objects(
        Bucket=glad_alerts_bucket, Prefix=glad_alerts_prefix
    )

    last_modified_datetimes = [obj["LastModified"] for obj in response["Contents"]]
    one_day_ago = _now() - timedelta(hours=24)

    return all(one_day_ago <= dt <= _now() for dt in last_modified_datetimes)


def get_daily_glad_dataset_ids():
    datasets = dict()
    datasets["gladalerts"] = deepcopy(
        AOI_DATASETS["gladalerts"]
    )  # only want to update glad alerts
    del datasets["gladalerts"]["summary"]  # don't need to update summary daily
    del datasets["gladalerts"]["whitelist"]

    return datasets


def _now():
    return datetime.now(tz.UTC)
