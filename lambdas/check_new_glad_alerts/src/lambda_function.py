from datetime import datetime, timedelta
from copy import deepcopy
import dateutil.tz as tz
import os
import json

from datapump_utils.geotrellis.emr_config import EMRConfig
from datapump_utils.s3 import s3_client, get_s3_path_parts
from datapump_utils.geotrellis.constants import (
    Analysis,
    FeatureType,
    FireType,
    FeatureSource,
)

GLAD_ALERTS_PATH = os.environ["GLAD_ALERTS_PATH"]
DATASETS = json.loads(os.environ["DATASETS"])
S3_BUCKET_PIPELINE = os.environ["S3_BUCKET_PIPELINE"]


def handler(event, context):
    new_alerts = check_for_new_glad_alerts_in_past_day()

    if new_alerts:
        emr_config_gadm = EMRConfig(30, "gladalerts-gadm-nightly")
        emr_config_geostore = EMRConfig(30, "gladalerts-geostore-nightly")
        emr_config_wdpa = EMRConfig(30, "gladalerts-wdpa-nightly")

        emr_config_gadm.add_step(
            analysis=Analysis.GLAD_ALERTS.value,
            feature_type=FeatureType.GADM.value,
            feature_sources=FeatureSource.GADM.value,
            summary=False,
        )

        emr_config_geostore.add_step(
            analysis=Analysis.GLAD_ALERTS.value,
            feature_type=FeatureType.GEOSTORE.value,
            feature_sources=FeatureSource.GEOSTORE.value,
            summary=False,
        )

        emr_config_wdpa.add_step(
            analysis=Analysis.GLAD_ALERTS.value,
            feature_type=FeatureType.WDPA.value,
            feature_sources=FeatureSource.WDPA.value,
            summary=False,
        )

        return {
            "status": "NEW_ALERTS_FOUND",
            "geostore": {
                "emr": {"config": emr_config_geostore.to_serializable()},
                "upload_type": "data-overwrite",
                "name": emr_config_geostore.name,
                "output_url": emr_config_geostore.output_url,
            },
            "gadm": {
                "emr": {"config": emr_config_gadm.to_serializable()},
                "upload_type": "data-overwrite",
                "name": emr_config_geostore.name,
                "output_url": emr_config_geostore.output_url,
            },
            "wdpa": {
                "emr": {"config": emr_config_wdpa.to_serializable()},
                "upload_type": "data-overwrite",
                "name": emr_config_geostore.name,
                "output_url": emr_config_geostore.output_url,
            },
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


def _now():
    return datetime.now(tz.UTC)
