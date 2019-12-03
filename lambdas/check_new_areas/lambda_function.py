import io
import json
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional, Tuple

import boto3
import requests
import yaml
from requests import Response
from shapely.wkb import dumps
from shapely.geometry import shape, Polygon

from geotrellis_summary_update.secrets import get_token
from geotrellis_summary_update.exceptions import EmptyResponseException
from geotrellis_summary_update.util import bucket_suffix, api_prefix


# environment should be set via environment variable. This can be done when deploying the lambda function.
if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"


S3_CLIENT = boto3.client("s3")
TOKEN: str = get_token()
PENDING_AOI_NAME = "pending_user_areas"

DIRNAME = os.path.dirname(__file__)

with open(os.path.join(DIRNAME, "analysis_config.yaml"), "r") as config:
    PENDING_AOI_ANALYSES = yaml.safe_load(config)


def handler(
    event: [Dict[str, Any]], context: [Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Main Lambda function
    """

    now: datetime = datetime.now()

    try:
        areas: Dict[str, Any] = get_pending_areas()
        geostore_ids: List[str] = get_geostore_ids(areas)
        geostore: Dict[str, Any] = get_geostore(geostore_ids)

        geostore_path = f"geotrellis/features/geostore/aoi-{now.strftime('%Y%m%d')}.tsv"
        with geostore_to_wkb(geostore) as wkb:
            S3_CLIENT.upload_fileobj(
                wkb,
                f"gfw-pipelines{bucket_suffix()}",
                f"geotrellis/features/geostore/aoi-{now.strftime('%Y%m%d')}.tsv",
            )

        return {
            "status": "FOUND_NEW",
            "feature_src": geostore_path,
            "feature_type": "geostore",
            "analyses": PENDING_AOI_ANALYSES[ENV],
            "env": ENV,
            "name": PENDING_AOI_NAME,
        }

    except EmptyResponseException:
        # slack_webhook("INFO", "No new user areas found. Doing nothing.")
        return {"status": "NOTHING_TO_DO"}
    except Exception:
        return {"status": "FAILED"}


def get_pending_areas() -> Dict[str, Any]:
    """
    Request to GFW API to get list of user areas which were recently submitted and need to be added to nightly updates
    """
    headers: Dict[str, str] = {"Authorization": f"Bearer {TOKEN}"}
    url: str = f"http://{api_prefix()}-api.globalforestwatch.org/v2/area?status=pending&all=true"
    r: Response = requests.get(url, headers=headers)

    if not r.json():
        raise EmptyResponseException("No pending areas")
    else:
        return r.json()


def get_geostore_ids(areas: Dict[str, Any]) -> List[str]:
    """
    Extract Geostore ID from user area
    """

    geostore_ids: List[str] = list()
    for area in areas["data"]:
        geostore_ids.append(area["attributes"]["geostore"])
    return geostore_ids


def get_geostore(geostore_ids: List[str]) -> Dict[str, Any]:
    """
    Get Geostore Geometry using list of geostore IDs
    """
    headers: Dict[str, str] = {"Authorization": f"Bearer {TOKEN}"}
    url: str = f"https://{api_prefix()}-api.globalforestwatch.org/v1/geostore/find-by-ids"
    r: Response = requests.post(url, data=json.dumps(geostore_ids), headers=headers)
    return r.json()


@contextmanager
def geostore_to_wkb(geostore: Dict[str, Any]) -> Iterator[io.StringIO]:
    """
    Convert Geojson to WKB. Slice geometries into 1x1 degree tiles
    """
    extent_1x1: List[Tuple[Polygon, bool, bool]] = _get_extent_1x1()
    wkb = io.StringIO()

    # Column Header
    wkb.write(f"geostore_id\tgeom\ttcd\tglad\n")

    # Body
    try:
        for g in geostore["data"]:
            geom: Polygon = shape(
                g["geostore"]["data"]["attributes"]["geojson"]["features"][0][
                    "geometry"
                ]
            )
            for tile in extent_1x1:
                if geom.intersects(tile[0]):
                    intersection = geom.intersection(tile[0])
                    wkb.write(
                        f"{g['geostoreId']}\t{dumps(intersection, hex=True)}\t{tile[1]}\t{tile[2]}\n"
                    )
        yield wkb

    finally:
        wkb.close()


def _get_extent_1x1() -> List[Tuple[Polygon, bool, bool]]:
    """
    Fetch 1x1 degree extent file
    """
    response: Dict[str, Any] = S3_CLIENT.get_object(
        Bucket=f"gfw-data-lake{bucket_suffix()}",
        Key="analysis_extent/latest/vector/extent_1x1.geojson",
    )

    glad_tiles: Dict[str, Any] = json.load(response["Body"])

    extent_1x1: List[Tuple[Polygon, bool, bool]] = list()

    for feature in glad_tiles["features"]:
        geom: Polygon = shape(feature["geometry"])
        extent_1x1.append(
            (geom, feature["properties"]["tcl"], feature["properties"]["glad"])
        )

    return extent_1x1
