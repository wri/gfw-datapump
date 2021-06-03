import geopandas as gd
import pandas as pd
import pysftp
import tarfile
import csv
from shapely.wkb import dumps
import numpy as np
import glob
import os
import boto3
import time

# from src.datapump.clients.aws import get_s3_client
# from src.datapump.globals import GLOBALS

WINDOWS = 25


def check_exists(day, year, sftp):
    day_str = f"{0 if day < 100 else ''}{0 if day < 10 else ''}{day}"
    fname = f"MCD64monthly.A{year}{day_str}.Win01.006.burndate"
    path = f"data/MODIS/C6/MCD64A1/SHP/Win01/{year}/{fname}.shapefiles.tar.gz"
    return sftp.exists(path)


def sync_burned_areas(day, year, sftp):
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
        df = gd.GeoDataFrame(pd.concat([df, window_df], ignore_index=True), crs=window_df.crs)

        # once loaded into memory, just immediately delete file since space is limited
        files = glob.glob(f"{fname}.*")
        for file in files:
            os.remove(file)

    # build lazy spatial index by evaluating it
    df.sindex

    # buffer(0) to rewrite the geometries in a way GEOS likes
    df['geometry'] = df.buffer(0)

    # dissolve all geometries with the same burn date value
    # note: this will also merge non-intersecting geometries with the same date into multipolygons
    df = df.dissolve(by='BurnDate')

    # explode will break out multipolygons into single polygon rows
    df = df.explode().reset_index()

    # convert BurnDate day-of-year value to standard datetime string
    year_start = np.datetime64(f"{year}-01-01", 'D')
    df["BurnDate"] = df["BurnDate"].apply(lambda day: year_start + np.timedelta64(day - 1, 'D')).dt.strftime("%Y-%m-%d")

    with open(f"modis_burned_areas_{year}{day_str}.csv", "w") as tsv_file:
        tsv_writer = csv.DictWriter(tsv_file, fieldnames=["alert__date", "geom"])
        tsv_writer.writeheader()

        for _, row in df.iterrows():
            tsv_writer.writerow({
                "alert__date": row["BurnDate"],
                "geom": dumps(row["geometry"], hex=True)
            })

    # upload to s3
    #get_s3_client().upload_file("monthly.tsv", GLOBALS.s3_bucket_data_lake, f"umd_modis_burned_areas/v2020/raw/tsv")
    # client = boto3.client()
    # get_s3_client().upload_file("monthly.tsv", GLOBALS.s3_bucket_data_lake, f"umd_modis_burned_areas/v2020/raw/tsv")


with pysftp.Connection('fuoco.geog.umd.edu', username='fire', password='burnt') as sftp:
    for year in range(2000, 2002):
        for day in range(1, 367):
            if check_exists(day, year, sftp):
                print(f"Syncing {year} {day}")
                start = time.time()
                sync_burned_areas(day, year, sftp)
                print(f"Sync took {time.time() - start} seconds")
