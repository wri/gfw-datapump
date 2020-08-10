import os
import json
import traceback

from datapump_utils.fire_alerts import process_active_fire_alerts, get_tmp_result_path
from datapump_utils.gpkg_util import update_geopackage
from datapump_utils.logger import get_logger
from datapump_utils.slack import slack_webhook

LOGGER = get_logger(__name__)
S3_BUCKET_PIPELINE = os.environ["S3_BUCKET_PIPELINE"]
DATASETS = json.loads(os.environ["DATASETS"])


def handler(event, context):
    if "manual" in event:
        modis_path = event["modis_path"]
        viirs_path = event["viirs_path"]

        if not isinstance(modis_path, list):
            modis_path = [modis_path]

        if not isinstance(viirs_path, list):
            viirs_path = [viirs_path]
    else:
        modis_path = [process_active_fire_alerts("MODIS")]
        viirs_path = [process_active_fire_alerts("VIIRS")]

        viirs_local_path = get_tmp_result_path("VIIRS")

        # try to update geopackage, but still move on if it fails
        try:
            update_geopackage(viirs_local_path)
        except Exception:
            LOGGER.error(f"Error updating fires geopackage: {traceback.format_exc()}")
            slack_webhook(
                "ERROR", "Error updating fires geopackage. Check logs for more details."
            )

    upload_type = "append"

    # get datasets
    viirs_datasets_geostore = {
        "firealerts_viirs": DATASETS["geostore"]["firealerts_viirs"]
    }
    modis_datasets_geostore = {
        "firealerts_modis": DATASETS["geostore"]["firealerts_modis"]
    }

    del viirs_datasets_geostore["firealerts_viirs"]["whitelist"]  # no summary
    del modis_datasets_geostore["firealerts_modis"]["whitelist"]  # no summary

    return {
        "viirs": {
            "gadm": {
                "instance_size": "r4.2xlarge",
                "instance_count": 3,
                "feature_src": "s3://gfw-files/2018_update/tsv/gadm36_adm2_1_1.csv",
                "feature_type": "gadm",
                "analyses": ["firealerts"],
                "datasets": {"firealerts_viirs": DATASETS["gadm"]["firealerts_viirs"]},
                "name": "fire-alerts-viirs-gadm",
                "upload_type": upload_type,
                "get_summary": False,
                "fire_config": {"viirs": viirs_path},
            },
            "wdpa": {
                "instance_size": "r4.2xlarge",
                "instance_count": 3,
                "feature_src": "s3://gfw-files/2018_update/tsv/wdpa_protected_areas_v201909_1_1.tsv",
                "feature_type": "wdpa",
                "analyses": ["firealerts"],
                "datasets": {"firealerts_viirs": DATASETS["wdpa"]["firealerts_viirs"]},
                "name": "fire-alerts-viirs-wdpa",
                "upload_type": upload_type,
                "get_summary": False,
                "fire_config": {"viirs": viirs_path},
            },
            "geostore": {
                "instance_size": "r4.2xlarge",
                "instance_count": 3,
                "feature_src": f"s3://{S3_BUCKET_PIPELINE}/geotrellis/features/geostore/*.tsv",
                "feature_type": "geostore",
                "analyses": ["firealerts"],
                "datasets": viirs_datasets_geostore,
                "name": "fire-alerts-viirs-geostore",
                "upload_type": upload_type,
                "get_summary": False,
                "fire_config": {"viirs": viirs_path},
            },
        },
        "modis": {
            "gadm": {
                "instance_size": "r4.2xlarge",
                "instance_count": 3,
                "feature_src": "s3://gfw-files/2018_update/tsv/gadm36_adm2_1_1.csv",
                "feature_type": "gadm",
                "analyses": ["firealerts"],
                "datasets": {"firealerts_modis": DATASETS["gadm"]["firealerts_modis"]},
                "name": "fire-alerts-modis-gadm",
                "upload_type": upload_type,
                "get_summary": False,
                "fire_config": {"modis": modis_path},
            },
            "wdpa": {
                "instance_size": "r4.2xlarge",
                "instance_count": 3,
                "feature_src": "s3://gfw-files/2018_update/tsv/wdpa_protected_areas_v201909_1_1.tsv",
                "feature_type": "wdpa",
                "analyses": ["firealerts"],
                "datasets": {"firealerts_modis": DATASETS["wdpa"]["firealerts_modis"]},
                "name": "fire-alerts-modis-wdpa",
                "upload_type": upload_type,
                "get_summary": False,
                "fire_config": {"modis": modis_path},
            },
            "geostore": {
                "instance_size": "r4.2xlarge",
                "instance_count": 3,
                "feature_src": f"s3://{S3_BUCKET_PIPELINE}/geotrellis/features/geostore/*.tsv",
                "feature_type": "geostore",
                "analyses": ["firealerts"],
                "datasets": modis_datasets_geostore,
                "name": "fire-alerts-modis-geostore",
                "upload_type": upload_type,
                "get_summary": False,
                "fire_src": modis_path,
                "fire_config": {"modis": modis_path},
            },
        },
    }
