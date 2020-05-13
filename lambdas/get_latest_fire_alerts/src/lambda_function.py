import traceback

from datapump_utils.fire_alerts import process_active_fire_alerts, get_tmp_result_path
from datapump_utils.gpkg_util import update_geopackage
from datapump_utils.logger import get_logger
from datapump_utils.slack import slack_webhook
from datapump_utils.geotrellis.emr_config import EMRConfig
from datapump_utils.geotrellis.constants import (
    Analysis,
    FeatureType,
    FireType,
    FeatureSource,
)

LOGGER = get_logger(__name__)

NAME = "firealerts-nightly"


def handler(event, context):
    modis_path = process_active_fire_alerts("MODIS")
    viirs_path = process_active_fire_alerts("VIIRS")

    viirs_local_path = get_tmp_result_path("VIIRS")

    # try to update geopackage, but still move on if it fails
    try:
        update_geopackage(viirs_local_path)
    except Exception:
        LOGGER.error(f"Error updating fires geopackage: {traceback.format_exc()}")
        slack_webhook(
            "ERROR", "Error updating fires geopackage. Check logs for more details."
        )

    config = _get_fire_emr_config(viirs_path, modis_path)

    return {
        "emr": {"config": config.to_serializable()},
        "upload_type": "append",
        "name": config.name,
        "output_url": config.output_url,
    }


def _get_fire_emr_config(viirs_path, modis_path):
    config = EMRConfig(worker_count=10, name=NAME)

    for feature_type in FeatureType:
        config.add_step(
            analysis=Analysis.FIRE_ALERTS.value,
            feature_type=feature_type.value,
            feature_sources=FeatureSource[feature_type.name].value,
            fire_type=FireType.VIIRS.value,
            fire_sources=viirs_path,
            summary=False,
            action_on_failure="CONTINUE",
        )

        config.add_step(
            analysis=Analysis.FIRE_ALERTS.value,
            feature_type=feature_type.value,
            feature_sources=FeatureSource[feature_type.name].value,
            fire_type=FireType.MODIS.value,
            fire_sources=modis_path,
            summary=False,
            action_on_failure="CONTINUE",
        )

    return config
