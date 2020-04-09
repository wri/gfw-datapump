import os
import json
import traceback

from datapump_utils.fire_alerts import process_active_fire_alerts

S3_BUCKET_PIPELINE = os.environ["S3_BUCKET_PIPELINE"]
DATASETS = json.loads(os.environ["DATASETS"])


def handler(event, context):
    modis_path = process_active_fire_alerts("MODIS")
    viirs_path = process_active_fire_alerts("VIIRS")

    upload_type = "append"

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
                "fire_config": {"viirs": [viirs_path]},
            },
            "geostore": {
                "instance_size": "r4.2xlarge",
                "instance_count": 3,
                "feature_src": f"s3://{S3_BUCKET_PIPELINE}/geotrellis/features/geostore/*.tsv",
                "feature_type": "geostore",
                "analyses": ["firealerts"],
                "datasets": {
                    "firealerts_viirs": DATASETS["geostore"]["firealerts_viirs"]
                },
                "name": "fire-alerts-viirs-geostore",
                "upload_type": upload_type,
                "get_summary": False,
                "fire_config": {"viirs": [viirs_path]},
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
                "fire_config": {"modis": [modis_path]},
            },
            "geostore": {
                "instance_size": "r4.2xlarge",
                "instance_count": 3,
                "feature_src": f"s3://{S3_BUCKET_PIPELINE}/geotrellis/features/geostore/*.tsv",
                "feature_type": "geostore",
                "analyses": ["firealerts"],
                "datasets": {
                    "firealerts_modis": DATASETS["geostore"]["firealerts_modis"]
                },
                "name": "fire-alerts-modis-geostore",
                "upload_type": upload_type,
                "get_summary": False,
                "fire_src": modis_path,
                "fire_config": {"modis": [modis_path]},
            },
        },
    }


"""
return {
    "modis": {
        "geostore": {
            "instance_size": "r4.2xlarge",
            "instance_count": 2,
            "feature_src": f"s3://{S3_BUCKET_PIPELINE}/geotrellis/features/geostore/*.tsv",
            "feature_type": "geostore",
            "analyses": ["firealerts"],
            "datasets": DATASETS["geostore"],
            "name": "fire-alerts-modis-geostore",
            "upload_type": upload_type,
            "get_summary": False,
            "fire_src": modis_path,
            "fire_type": "modis",
        },
        "gadm": {
            "instance_size": "r4.2xlarge",
            "instance_count": 6,
            "feature_src": "s3://gfw-files/2018_update/tsv/gadm36_adm2_1_1.csv",
            "feature_type": "gadm",
            "analyses": ["firealerts"],
            "datasets": DATASETS["gadm"],
            "name": "fire-alerts-modis-gadm",
            "upload_type": upload_type,
            "get_summary": False,
            "fire_src": modis_path,
            "fire_type": "modis",
        },
        "wdpa": {
            "instance_size": "r4.2xlarge",
            "instance_count": 6,
            "feature_src": "s3://gfw-files/2018_update/tsv/wdpa_protected_areas_v201909_1_1.tsv",
            "feature_type": "wdpa",
            "analyses": ["firealerts"],
            "datasets": DATASETS["wdpa"],
            "name": "fire-alerts-modis-wdpa",
            "upload_type": upload_type,
            "get_summary": False,
            "fire_src": modis_path,
            "fire_type": "modis",
        },
    },
    "viirs": {
        "geostore": {
            "instance_size": "r4.2xlarge",
            "instance_count": 2,
            "feature_src": f"s3://{S3_BUCKET_PIPELINE}/geotrellis/features/geostore/*.tsv",
            "feature_type": "geostore",
            "analyses": ["firealerts"],
            "datasets": DATASETS["geostore"],
            "name": "fire-alerts-viirs-geostore",
            "upload_type": upload_type,
            "get_summary": False,
            "fire_src": viirs_path,
            "fire_type": "viirs",
        },

        "wdpa": {
            "instance_size": "r4.2xlarge",
            "instance_count": 6,
            "feature_src": "s3://gfw-files/2018_update/tsv/wdpa_protected_areas_v201909_1_1.tsv",
            "feature_type": "wdpa",
            "analyses": ["firealerts"],
            "datasets": DATASETS["wdpa"],
            "name": "fire-alerts-viirs-wdpa",
            "upload_type": upload_type,
            "get_summary": False,
            "fire_src": viirs_path,
            "fire_type": "viirs",
        },
    },
}
"""
