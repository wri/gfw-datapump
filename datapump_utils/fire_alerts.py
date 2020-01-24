import requests
import csv
import os

from datapump_utils.util import get_date_string
from datapump_utils.s3 import s3_client

ACTIVE_FIRE_ALERTS_24HR_CSV_URLS = {
    "MODIS": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/c6/csv/MODIS_C6_Global_24h.csv",
    "VIIRS": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/viirs/csv/VNP14IMGTDL_NRT_Global_24h.csv",
}
DATA_LAKE_BUCKET = os.environ["S3_BUCKET_DATA_LAKE"]
PIPELINE_BUCKET = os.environ["S3_BUCKET_PIPELINE"]


def process_active_fire_alerts(alert_type):
    response = requests.get(ACTIVE_FIRE_ALERTS_24HR_CSV_URLS[alert_type])

    if response.status_code != 200:
        raise Exception(
            f"Unable to get active {alert_type} fire alerts, FIRMS returned status code {response.status_code}"
        )

    csv_reader = csv.DictReader(response.text.splitlines(), delimiter=",")
    fields = [
        "latitude",
        "longitude",
        "acq_date",
        "confidence",
        "brightness",
        "bright_ti4",
        "bright_t31",
        "bright_ti5",
        "frp",
    ]
    result_name = f"{alert_type}_{get_date_string()}"

    tsv_file = open(f"{result_name}.tsv", "w", newline="")
    tsv_writer = csv.DictWriter(tsv_file, fieldnames=fields, delimiter="\t")
    tsv_writer.writeheader()

    for row in csv_reader:
        tsv_row = dict()
        for field in fields:
            if field in row:
                tsv_row[field] = row[field]

        tsv_writer.writerow(tsv_row)

    tsv_file.close()

    # upload both files to s3
    with open(f"{result_name}.tsv", "rb") as tsv_result:
        pipeline_key = (
            f"{alert_type}_active_fire_alerts/vector/espg-4326/tsv/{result_name}.tsv"
        )
        s3_client().upload_fileobj(tsv_result, Bucket=PIPELINE_BUCKET, Key=pipeline_key)
