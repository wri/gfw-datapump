from datapump_utils.fire_alerts import process_active_fire_alerts


def handler(event, context):
    process_active_fire_alerts("MODIS")
    process_active_fire_alerts("VIIRS")
