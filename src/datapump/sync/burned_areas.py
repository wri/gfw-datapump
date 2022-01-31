import csv
import glob
import os
import tarfile
from datetime import datetime
from typing import List, Tuple

import geopandas as gd
import numpy as np
import pandas as pd
import pysftp
from shapely.wkb import dumps

from src.datapump.clients.aws import get_s3_client
from src.datapump.globals import GLOBALS, LOGGER

WINDOWS = 25
S3_RAW_DIR = "umd_modis_burned_areas/raw"


def check_exists(day: int, year: int, sftp: pysftp.Connection) -> bool:
    """
    Check UMD FTP server to see if a file exists for a certain day/year
    """
    day_str = f"{0 if day < 100 else ''}{0 if day < 10 else ''}{day}"
    fname = f"MCD64monthly.A{year}{day_str}.Win01.006.burndate"
    path = f"data/MODIS/C6/MCD64A1/SHP/Win01/{year}/{fname}.shapefiles.tar.gz"
    return sftp.exists(path)


def get_last_synced_date() -> Tuple[int, int]:
    """
    Get the last day we synced data in S3 from the UMD FTP server by checking the last day/year uploaded.
    """
    resp = get_s3_client().list_objects(
        Bucket=GLOBALS.s3_bucket_data_lake, Prefix=f"{S3_RAW_DIR}/"
    )
    if "Contents" in resp:
        last_file = resp["Contents"][-1]
        last_day = last_file["Key"][-7:-4]
        last_year = last_file["Key"][-11:-7]

        return int(last_day), int(last_year)
    else:
        # start of MODIS if empty
        return 1, 2000


def sync_burned_areas(day: int, year: int, sftp: pysftp.Connection) -> str:
    """
    Download SHP files from UMD FTP server, process and upload as WKB CSVs to S3.

    UMD stores the data in various "window" across the world, based on common areas
    for users to analyze burned areas. These windows intersect each other, so to get
    the global view of burned areas, we need to dissolve all the geometries based on
    burn date.
    """
    df = gd.GeoDataFrame()

    for i in range(1, WINDOWS):
        day_str = f"{0 if day < 100 else ''}{0 if day < 10 else ''}{day}"
        window = f"Win{0 if i < 10 else ''}{i}"
        fname = f"MCD64monthly.A{year}{day_str}.{window}.006.burndate"
        path = f"data/MODIS/C6/MCD64A1/SHP/{window}/{year}/{fname}.shapefiles.tar.gz"
        sftp.get(path)

        with tarfile.open(f"{fname}.shapefiles.tar.gz", "r:gz") as tar:
            tar.extractall()

        window_df = gd.read_file(f"{fname}.shp")
        df = gd.GeoDataFrame(
            pd.concat([df, window_df], ignore_index=True), crs=window_df.crs
        )

        # once loaded into memory, just immediately delete file since space is limited
        files = glob.glob(f"{fname}.*")
        for file in files:
            os.remove(file)

    # build lazy spatial index by evaluating it
    df.sindex

    # buffer(0) to rewrite the geometries in a way GEOS likes
    df["geometry"] = df.buffer(0)

    # dissolve all geometries with the same burn date value
    # note: this will also merge non-intersecting geometries with the same date into multipolygons
    df = df.dissolve(by="BurnDate")

    # explode will break out multipolygons into single polygon rows
    df = df.explode().reset_index()

    # convert BurnDate day-of-year value to standard datetime string
    year_start = np.datetime64(f"{year}-01-01", "D")
    df["BurnDate"] = (
        df["BurnDate"]
        .apply(lambda day: year_start + np.timedelta64(day - 1, "D"))
        .dt.strftime("%Y-%m-%d")
    )

    burned_areas_name = f"modis_burned_areas_{year}{day_str}.csv"
    burned_areas_path = f"/tmp/{burned_areas_name}"
    with open(burned_areas_path, "w") as tsv_file:
        tsv_writer = csv.DictWriter(tsv_file, fieldnames=["alert__date", "geom"])
        tsv_writer.writeheader()

        for _, row in df.iterrows():
            tsv_writer.writerow(
                {
                    "alert__date": row["BurnDate"],
                    "geom": dumps(row["geometry"], hex=True),
                }
            )

    # upload to s3
    burned_areas_s3_key = f"{S3_RAW_DIR}/{burned_areas_name}"
    get_s3_client().upload_file(
        burned_areas_path, GLOBALS.s3_bucket_data_lake, burned_areas_s3_key
    )
    return f"s3://{burned_areas_s3_key}"


def get_dates_to_check(last_day: int, last_year: int, now_day: int, now_year: int):
    """
    Generate all day/year combos to check, potentially across a year boundary
    """
    if last_year == now_year:
        return [(day, last_year) for day in range(last_day + 1, now_day)]
    else:
        last_years_days = [(day, last_year) for day in range(last_day + 1, 367)]
        this_years_days = [(day, now_year) for day in range(1, now_day)]
        return last_years_days + this_years_days


def sync_burned_areas_if_exists() -> List[str]:
    with pysftp.Connection(
        # TODO get from secrets
    ) as sftp:
        last_synced_day, last_synced_year = get_last_synced_date()
        now = datetime.now()

        dates_to_check = get_dates_to_check(
            last_synced_day, last_synced_year, now.day, now.year
        )
        burned_area_uris = []
        for day, year in dates_to_check:
            if check_exists(day, year, sftp):
                LOGGER.info(f"Syncing {now.day} {now.year}")
                burned_area_uris.append(sync_burned_areas(now.day, now.year, sftp))

        return burned_area_uris
