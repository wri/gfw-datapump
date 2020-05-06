from enum import Enum
import os

S3_BUCKET_PIPELINE = os.environ["S3_BUCKET_PIPELINE"]
S3_BUCKET_DATA_LAKE = os.environ["S3_BUCKET_DATA_LAKE"]


class Analysis(Enum):
    ANNUAL_UPDATE_MINIMAL = "annualupdate_minimal"
    GLAD_ALERTS = "gladalerts"
    FIRE_ALERTS = "firealerts"


class FeatureType(Enum):
    GADM = "gadm"
    WDPA = "wdpa"
    GEOSTORE = "geostore"


class FeatureSource(Enum):
    GADM = "s3://gfw-files/2018_update/tsv/gadm36_adm2_1_1.csv"
    WDPA = "s3://gfw-files/2018_update/tsv/wdpa_protected_areas_v201909_1_1.tsv"
    GEOSTORE = f"s3://{S3_BUCKET_PIPELINE}/geotrellis/features/geostore/*.tsv"


class FireType(Enum):
    VIIRS = "viirs"
    MODIS = "modis"


class FireSources(Enum):
    VIIRS = [
        f"s3://{S3_BUCKET_DATA_LAKE}/nasa_viirs_fire_alerts/v1/vector/epsg-4326/tsv/near_real_time/*.tsv",
        f"s3://{S3_BUCKET_DATA_LAKE}nasa_viirs_fire_alerts/v1/vector/epsg-4326/tsv/scientific/*.tsv",
    ]
    MODIS = [
        f"s3://{S3_BUCKET_DATA_LAKE}nasa_modis_fire_alerts/v6/vector/epsg-4326/tsv/near_real_time/*.tsv",
        f"s3://{S3_BUCKET_DATA_LAKE}/nasa_modis_fire_alerts/v6/vector/epsg-4326/tsv/scientific/*.tsv",
    ]
