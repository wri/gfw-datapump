import csv
import io
import os
import shutil
import zipfile

import requests
import shapefile

from ..clients.aws import get_s3_client
from ..globals import LOGGER

ACTIVE_FIRE_ALERTS_48HR_CSV_URLS = {
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
    LOGGER.info(f"Retrieving fire alerts for {alert_type}")
    response = requests.get(ACTIVE_FIRE_ALERTS_48HR_CSV_URLS[alert_type])

    if response.status_code != 200:
        raise Exception(
            f"Unable to get active {alert_type} fire alerts, FIRMS returned status code {response.status_code}"
        )

    LOGGER.info("Successfully download alerts from NASA")

    zip = zipfile.ZipFile(io.BytesIO(response.content))
    shp_dir = f"{TEMP_DIR}/fire_alerts_{alert_type}"
    zip.extractall(shp_dir)
    sf = shapefile.Reader(f"{shp_dir}/{SHP_NAMES[alert_type]}")

    rows = []
    for shape_record in sf.iterShapeRecords():
        row = shape_record.record.as_dict()
        row["LATITUDE"] = shape_record.shape.points[0][1]
        row["LONGITUDE"] = shape_record.shape.points[0][0]
        row["ACQ_DATE"] = row["ACQ_DATE"].strftime("%Y-%m-%d")
        rows.append(row)

    sorted_rows = sorted(rows, key=lambda row: f"{row['ACQ_DATE']}_{row['ACQ_TIME']}")

    last_row = sorted_rows[-1]

    fields = [
        "latitude",
        "longitude",
        "acq_date",
        "acq_time",
        "confidence",
    ]
    fields += BRIGHTNESS_FIELDS[alert_type]
    fields.append("frp")

    result_path = get_tmp_result_path(alert_type)

    tsv_file = open(result_path, "w", newline="")
    tsv_writer = csv.DictWriter(tsv_file, fieldnames=fields, delimiter="\t")
    tsv_writer.writeheader()

    nrt_s3_directory = f"nasa_{alert_type.lower()}_fire_alerts/{VERSIONS[alert_type]}/vector/epsg-4326/tsv/near_real_time"
    last_saved_date, last_saved_min = _get_last_saved_alert_time(nrt_s3_directory)
    LOGGER.info(f"Last saved row datetime: {last_saved_date} {last_saved_min}")

    first_row = None
    for row in sorted_rows:
        # only start once we confirm we're past the overlap with the last dataset
        if row["ACQ_DATE"] > last_saved_date or (
            row["ACQ_DATE"] == last_saved_date and row["ACQ_TIME"] > last_saved_min
        ):
            if not first_row:
                first_row = row
                LOGGER.info(
                    f"First row datetime: {first_row['ACQ_DATE']} {first_row['ACQ_TIME']}"
                )

            # for VIIRS, we only want first letter of confidence category, to make NRT category same as scientific
            if alert_type == "viirs":
                row["CONFIDENCE"] = row["CONFIDENCE"][0]

            _write_row(row, fields, tsv_writer)

    LOGGER.info(f"Last row datetime: {last_row['ACQ_DATE']} {last_row['ACQ_TIME']}")
    LOGGER.info("Successfully wrote TSV")

    tsv_file.close()

    # upload both files to s3
    file_name = f"{first_row['ACQ_DATE']}-{first_row['ACQ_TIME']}_{last_row['ACQ_DATE']}-{last_row['ACQ_TIME']}.tsv"

    with open(result_path, "rb") as tsv_result:
        pipeline_key = f"{nrt_s3_directory}/{file_name}"
        get_s3_client().upload_fileobj(
            tsv_result, Bucket=DATA_LAKE_BUCKET, Key=pipeline_key
        )

    LOGGER.info(f"Successfully uploaded to s3://{DATA_LAKE_BUCKET}/{pipeline_key}")

    # remove raw shapefile, since it can be big and hit max lambda storage size of 512 MB
    shutil.rmtree(shp_dir)

    return (f"s3a://{DATA_LAKE_BUCKET}/{pipeline_key}", last_row["ACQ_DATE"])


def get_tmp_result_path(alert_type):
    return f"{TEMP_DIR}/fire_alerts_{alert_type.lower()}.tsv"


def _get_last_saved_alert_time(nrt_s3_directory):
    response = get_s3_client().list_objects(
        Bucket=DATA_LAKE_BUCKET, Prefix=f"{nrt_s3_directory}/"
    )

    if "Contents" in response:
        last_file = response["Contents"][-1]
        last_min = last_file["Key"][-8:-4]
        last_date = last_file["Key"][-19:-9]

        return last_date, last_min
    else:
        return "0000-00-00", "0000"


def _write_row(row, fields, writer):
    tsv_row = dict()
    for field in fields:
        if field.upper() in row:
            tsv_row[field] = row[field.upper()]

    writer.writerow(tsv_row)
