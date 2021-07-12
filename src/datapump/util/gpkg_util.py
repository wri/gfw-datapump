import csv
import os
import sqlite3
import subprocess
from datetime import datetime, timedelta

import boto3


def get_bucket():
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(os.environ["S3_BUCKET_PIPELINE"])

    return bucket


def download_gpkg():
    # weirdly this seems 2x - 3x as fast as reading directly from s3
    # maybe spatial index isn't used when reading from s3?
    bucket = get_bucket()

    gpkg_src = (
        "fires/data.gpkg"  # "nasa_viirs_fire_alerts/v1/vector/epsg-4326/gpkg/data.gpkg"
    )
    local_gpkg = "/tmp/data.gpkg"
    bucket.download_file(gpkg_src, local_gpkg)

    return local_gpkg


def delete_dups_and_old_fires(src_gpkg):
    # get the date of 10 days ago
    date_10_days_ago = datetime.now() - timedelta(days=10)
    date_10_days_ago = date_10_days_ago.strftime("%Y-%m-%d")

    # connect to GPKG and delete any duplicate data
    conn = sqlite3.connect(src_gpkg)
    cur = conn.cursor()

    sql_str = (
        "DELETE FROM data "
        "WHERE rowid NOT IN ( "
        "SELECT min(rowid) "
        "FROM data "
        "GROUP BY geom, fire_date);"
    )
    cur.execute(sql_str)

    delete_old_fires_sql = "DELETE FROM data " 'WHERE fire_date <= "{}"'.format(
        date_10_days_ago
    )

    cur.execute(delete_old_fires_sql)
    conn.commit()
    conn.close()


def upload_gpkg(src_gpkg):
    bucket = get_bucket()
    gpkg_dst = "fires/data.gpkg"

    bucket.upload_file(src_gpkg, gpkg_dst)


def update_geopackage(fires_path):
    # Read fires csv
    with open(fires_path, newline="") as fires_file:
        fires = [row for row in csv.DictReader(fires_file, delimiter="\t")]

    # open source geopackage to write new data
    src_gpkg = download_gpkg()

    # read in csv and write it back with correct format
    new_rows_list = fix_csv_date_lines(fires)

    # make vrt of source fires
    fires_vrt = create_vrt(new_rows_list)

    # append new fires to gpkg
    cmd = [
        "/opt/bin/ogr2ogr",
        "-append",
        src_gpkg,
        fires_vrt,
        "-f",
        "GPKG",
        "-nln",
        "data",
    ]
    subprocess.check_call(cmd)

    # remove old and duplicate points
    delete_dups_and_old_fires(src_gpkg)

    # upload gpkg back to s3
    upload_gpkg(src_gpkg)

    return None


def fix_csv_date_lines(in_lines):
    output_rows = []

    for line in in_lines:
        lat = line["latitude"]
        lon = line["longitude"]
        fire_date = line["acq_date"]

        new_row = [lat, lon, fire_date]
        output_rows.append(new_row)

    return output_rows


def create_vrt(in_rows):
    fires_formatted = "/tmp/fires_formatted.csv"
    fires_formatted_date = open(fires_formatted, "w")
    writer = csv.writer(fires_formatted_date)

    header_row = ["latitude", "longitude", "fire_date"]
    writer.writerow(header_row)

    # write all data
    writer.writerows(in_rows)

    fires_formatted_date.close()

    lyr_name = fires_formatted.strip(".csv")
    lyr_name = lyr_name.split("/")[-1:][0]
    fires_vrt = "/tmp/fires.vrt"
    vrt_text = """<OGRVRTDataSource>
                    <OGRVRTLayer name="{0}">
                    <SrcDataSource relativeToVRT="1">{0}.csv</SrcDataSource>
                    <GeometryType>wkbPoint</GeometryType>
                    <LayerSRS>WGS84</LayerSRS>
                    <GeometryField encoding="PointFromColumns" y="longitude" x="latitude"/>
                  </OGRVRTLayer>
                </OGRVRTDataSource>""".format(
        lyr_name
    )

    with open(fires_vrt, "w") as thefile:
        thefile.write(vrt_text)

    return fires_vrt
