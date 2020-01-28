import requests
import csv
import os

from datapump_utils.util import get_date_string
from datapump_utils.s3 import s3_client

ACTIVE_FIRE_ALERTS_48HR_CSV_URLS = {
    "MODIS": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/c6/csv/MODIS_C6_Global_48h.csv",
    "VIIRS": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/viirs/csv/VNP14IMGTDL_NRT_Global_48h.csv",
}
DATA_LAKE_BUCKET = os.environ["S3_BUCKET_DATA_LAKE"]
BRIGHTNESS_FIELDS = {
    "MODIS": ["brightness", "bright_t31"],
    "VIIRS": ["bright_ti4", "bright_ti5"],
}
VERSIONS = {"MODIS": "v6", "VIIRS": "v1"}


def process_active_fire_alerts(alert_type):
    response = requests.get(ACTIVE_FIRE_ALERTS_48HR_CSV_URLS[alert_type])

    if response.status_code != 200:
        raise Exception(
            f"Unable to get active {alert_type} fire alerts, FIRMS returned status code {response.status_code}"
        )

    lines = response.text.splitlines()
    csv_reader = csv.DictReader(lines, delimiter=",")
    sorted_rows = sorted(
        csv_reader, key=lambda row: f"{row['acq_date']}_{row['acq_time']}"
    )

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

    result_name = f"fire_alerts_{alert_type.lower()}"

    tsv_file = open(f"{result_name}.tsv", "w", newline="")
    tsv_writer = csv.DictWriter(tsv_file, fieldnames=fields, delimiter="\t")
    tsv_writer.writeheader()

    nrt_s3_directory = f"nasa_{alert_type.lower()}_fire_alerts/{VERSIONS[alert_type]}/vector/espg-4326/nrt"
    last_saved_date, last_saved_min = _get_last_saved_alert_time(nrt_s3_directory)

    first_row = None
    for row in sorted_rows:
        # only start once we confirm we're past the overlap with the last dataset
        if row["acq_date"] >= last_saved_date and row["acq_time"] > last_saved_min:
            if not first_row:
                first_row = row

            _write_row(row, fields, tsv_writer)

    tsv_file.close()

    # upload both files to s3
    file_name = f"{first_row['acq_date']}-{first_row['acq_time']}_{last_row['acq_date']}-{last_row['acq_time']}.tsv"
    with open(f"{result_name}.tsv", "rb") as tsv_result:
        pipeline_key = f"{nrt_s3_directory}/{file_name}"
        s3_client().upload_fileobj(
            tsv_result, Bucket=DATA_LAKE_BUCKET, Key=pipeline_key
        )


def _get_last_saved_alert_time(nrt_s3_directory):
    response = s3_client().list_objects(
        Bucket=DATA_LAKE_BUCKET, Prefix=nrt_s3_directory
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
        if field in row:
            tsv_row[field] = row[field]

    writer.writerow(tsv_row)
