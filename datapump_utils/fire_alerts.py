from geojson import Feature, FeatureCollection, Point
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


def process_active_fire_alerts(alert_type):
    response = requests.get(ACTIVE_FIRE_ALERTS_24HR_CSV_URLS[alert_type])
    csv_reader = csv.DictReader(response.text.splitlines(), delimiter=",")

    result_name = f"{alert_type}_{get_date_string()}"
    key = f"{alert_type}_active_fire_alerts/vector/espg-4326/{result_name}"

    tsv_file = open(f"{result_name}.tsv", "w", newline="")
    tsv_writer = csv.DictWriter(
        tsv_file, fieldnames=csv_reader.fieldnames, delimiter="\t"
    )
    tsv_writer.writeheader()

    features = []
    for row in csv_reader:
        # write lat, lon to tsv file
        tsv_writer.writerow(row)

        # add to in-memory geojson
        geom = Point((float(row["longitude"]), float(row["latitude"])))
        del row["latitude"]
        del row["longitude"]

        features.append(Feature(geometry=geom, properties=row))

    tsv_file.close()

    collection = FeatureCollection(features)
    with open(f"{result_name}.geojson", "w") as geojson:
        geojson.write("%s" % collection)

    # upload both files to s3
    with open(f"{result_name}.tsv", "rb") as tsv_result:
        s3_client().upload_fileobj(
            tsv_result, Bucket=DATA_LAKE_BUCKET, Key=f"{key}.tsv"
        )

    with open(f"{result_name}.geojson", "rb") as geojson_result:
        s3_client().upload_fileobj(
            geojson_result, Bucket=DATA_LAKE_BUCKET, Key=f"{key}.geojson"
        )
