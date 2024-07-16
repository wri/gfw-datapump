import csv
import os
from tempfile import TemporaryDirectory

import shapefile

from ..clients.aws import get_s3_client
from ..globals import LOGGER

ACTIVE_FIRE_ALERTS_7D_SHAPEFILE_URLS = {
    "modis": "https://firms2.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/shapes/zips/MODIS_C6_1_Global_7d.zip",
    "viirs": "https://firms2.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/shapes/zips/SUOMI_VIIRS_C2_Global_7d.zip",
}

DATA_LAKE_BUCKET = os.environ["S3_BUCKET_DATA_LAKE"]
BRIGHTNESS_FIELDS = {
    "modis": ["brightness", "bright_t31"],
    "viirs": ["bright_ti4", "bright_ti5"],
}
VERSIONS = {"modis": "v6", "viirs": "v1"}
SHP_NAMES = {
    "viirs": "SUOMI_VIIRS_C2_Global_7d.shp",
    "modis": "MODIS_C6_1_Global_7d.shp",
}

TEMP_DIR = "/tmp"


def process_active_fire_alerts(alert_type):
    nrt_s3_directory = f"nasa_{alert_type.lower()}_fire_alerts/{VERSIONS[alert_type]}/vector/epsg-4326/tsv/near_real_time"
    last_saved_date, last_saved_min = _get_last_saved_alert_time(nrt_s3_directory)
    LOGGER.info(f"Last saved row datetime: {last_saved_date} {last_saved_min}")

    LOGGER.info(f"Retrieving fire alerts for {alert_type}")
    rows = []
    with shapefile.Reader(ACTIVE_FIRE_ALERTS_7D_SHAPEFILE_URLS[alert_type]) as sf:
        LOGGER.info(f"Shapefile has {len(sf)} records")
        for shape_record in sf.iterShapeRecords():
            row = shape_record.record.as_dict()
            row["ACQ_DATE"] = row["ACQ_DATE"].strftime("%Y-%m-%d")
            row["LATITUDE"] = shape_record.shape.points[0][1]
            row["LONGITUDE"] = shape_record.shape.points[0][0]
            # For VIIRS we only want first letter of confidence category,
            # to make NRT category same as scientific
            if alert_type == "viirs":
                row["CONFIDENCE"] = row["CONFIDENCE"][0]

            if row["ACQ_DATE"] > last_saved_date or (
                row["ACQ_DATE"] == last_saved_date and
                row["ACQ_TIME"] > last_saved_min
            ):
                rows.append(row)

    if not rows:
        raise Exception(
            f"{alert_type} shapefile contained no new records since {last_saved_date} {last_saved_min}"
        )
    else:
        LOGGER.info(f"Found {len(rows)} new records for {alert_type}")

    sorted_rows = sorted(rows, key=lambda row: f"{row['ACQ_DATE']}_{row['ACQ_TIME']}")

    first_row = sorted_rows[0]
    last_row = sorted_rows[-1]

    LOGGER.info(f"First new record datetime: {first_row['ACQ_DATE']} {first_row['ACQ_TIME']}")

    fields = [
        "latitude",
        "longitude",
        "acq_date",
        "acq_time",
        "confidence",
        *(BRIGHTNESS_FIELDS[alert_type]),
        "frp"
    ]

    with TemporaryDirectory() as temp_dir:
        result_path = f"{temp_dir}/fire_alerts_{alert_type.lower()}.tsv"

        with open(result_path, "w", newline="") as tsv_file:
            tsv_writer = csv.DictWriter(tsv_file, fieldnames=fields, delimiter="\t")
            tsv_writer.writeheader()

            for row in sorted_rows:
                _write_row(row, fields, tsv_writer)

        LOGGER.info("Successfully wrote TSV")
        LOGGER.info(f"Last new record datetime: {last_row['ACQ_DATE']} {last_row['ACQ_TIME']}")

        # Upload file to s3
        pipeline_key = f"{nrt_s3_directory}/{first_row['ACQ_DATE']}-{first_row['ACQ_TIME']}_{last_row['ACQ_DATE']}-{last_row['ACQ_TIME']}.tsv"

        with open(result_path, "rb") as tsv_result:
            get_s3_client().upload_fileobj(
                tsv_result, Bucket=DATA_LAKE_BUCKET, Key=pipeline_key
            )

    LOGGER.info(f"Successfully uploaded to s3://{DATA_LAKE_BUCKET}/{pipeline_key}")

    return (f"s3a://{DATA_LAKE_BUCKET}/{pipeline_key}", last_row["ACQ_DATE"])


def get_tmp_result_path(alert_type):
    return f"{TEMP_DIR}/fire_alerts_{alert_type.lower()}.tsv"


def _get_last_saved_alert_time(nrt_s3_directory):
    paginator = get_s3_client().get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(Bucket=DATA_LAKE_BUCKET, Prefix=nrt_s3_directory)
    latest_key = None

    for page in page_iterator:
        if "Contents" in page:
            latest_key_curr = max(page['Contents'], key=lambda x: x["Key"])["Key"]
            if latest_key is None or latest_key_curr > latest_key:
                latest_key = latest_key_curr

    if latest_key:
        last_min = latest_key[-8:-4]
        last_date = latest_key[-19:-9]

        return last_date, last_min
    else:
        return "0000-00-00", "0000"


def _write_row(row, fields, writer):
    tsv_row = dict()
    for field in fields:
        if field.upper() in row:
            tsv_row[field] = row[field.upper()]

    writer.writerow(tsv_row)
