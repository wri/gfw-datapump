import csv
import glob
import io
import os
import tempfile
import zipfile

import requests
import shapefile

from ..clients.aws import get_s3_client
from ..globals import LOGGER

# VIIRS uses NOAA-20, since Suomi NPP data delivery ceases on 2026-11-02. Either URL
# can be overridden with the env var <ALERT_TYPE>_FIRE_ALERTS_URL (e.g.
# VIIRS_FIRE_ALERTS_URL) to switch satellites without a code change.
ACTIVE_FIRE_ALERTS_7D_SHAPEFILE_URLS = {
    "modis": "https://firms2.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/shapes/zips/MODIS_C6_1_Global_7d.zip",
    "viirs": "https://firms2.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/shapes/zips/J1_VIIRS_C2_Global_7d.zip",
}

DATA_LAKE_BUCKET = os.environ["S3_BUCKET_DATA_LAKE"]
BRIGHTNESS_FIELDS = {
    "modis": ["brightness", "bright_t31"],
    "viirs": ["bright_ti4", "bright_ti5"],
}
VERSIONS = {"modis": "v6", "viirs": "v1"}

TEMP_DIR = "/tmp"


def process_active_fire_alerts(alert_type):
    """
    Download the latest 7-day FIRMS alerts and upload any alerts newer than the
    last saved NRT file to S3 as a TSV.
    :return: (S3 URI of the new TSV, last alert date), or (None, None) if there
        are no new alerts to sync
    """
    url = os.environ.get(
        f"{alert_type.upper()}_FIRE_ALERTS_URL",
        ACTIVE_FIRE_ALERTS_7D_SHAPEFILE_URLS[alert_type],
    )
    LOGGER.info(f"Retrieving fire alerts for {alert_type} from {url}")
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(
            f"Unable to get active {alert_type} fire alerts, FIRMS returned status code {response.status_code}"
        )

    LOGGER.info("Successfully downloaded alerts from NASA")

    # Extract to a temporary directory that is always removed, since the raw shapefile
    # can be big and hit max lambda storage size of 512 MB
    rows = []
    with tempfile.TemporaryDirectory(
        prefix=f"fire_alerts_{alert_type}_", dir=TEMP_DIR
    ) as shp_dir:
        zip = zipfile.ZipFile(io.BytesIO(response.content))
        zip.extractall(shp_dir)

        # Find the shapefile rather than hardcoding its name, since the name depends on
        # the satellite (e.g. J1_VIIRS_C2_Global_7d.shp for NOAA-20).
        shp_paths = glob.glob(f"{shp_dir}/*.shp")
        if len(shp_paths) != 1:
            raise Exception(
                f"{alert_type} fire alerts zip downloaded, but contains {len(shp_paths)} .shp files, expected 1!"
            )

        with shapefile.Reader(shp_paths[0]) as sf:
            for shape_record in sf.iterShapeRecords():
                row = shape_record.record.as_dict()
                row["LATITUDE"] = shape_record.shape.points[0][1]
                row["LONGITUDE"] = shape_record.shape.points[0][0]
                row["ACQ_DATE"] = row["ACQ_DATE"].strftime("%Y-%m-%d")
                rows.append(row)

    if not rows:
        LOGGER.warning(f"{alert_type} fire alerts file from {url} has no alerts, skipping sync")
        return None, None

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

    nrt_s3_directory = f"nasa_{alert_type.lower()}_fire_alerts/{VERSIONS[alert_type]}/vector/epsg-4326/tsv/near_real_time"
    last_saved_date, last_saved_min = _get_last_saved_alert_time(nrt_s3_directory)
    LOGGER.info(f"Last saved row datetime: {last_saved_date} {last_saved_min}")

    if not _is_after(last_row, last_saved_date, last_saved_min):
        LOGGER.warning(
            f"No {alert_type} fire alerts newer than last saved alert "
            f"({last_saved_date} {last_saved_min}), skipping sync"
        )
        return None, None

    result_path = get_tmp_result_path(alert_type)

    tsv_file = open(result_path, "w", newline="")
    tsv_writer = csv.DictWriter(tsv_file, fieldnames=fields, delimiter="\t")
    tsv_writer.writeheader()

    first_row = None
    for row in sorted_rows:
        # only start once we confirm we're past the overlap with the last dataset
        if _is_after(row, last_saved_date, last_saved_min):
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


def _is_after(row, last_date, last_min):
    return row["ACQ_DATE"] > last_date or (
        row["ACQ_DATE"] == last_date and row["ACQ_TIME"] > last_min
    )


def _write_row(row, fields, writer):
    tsv_row = dict()
    for field in fields:
        if field.upper() in row:
            tsv_row[field] = row[field.upper()]

    writer.writerow(tsv_row)
