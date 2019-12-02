import io
import json
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional, Tuple

import boto3
import requests
from requests import Response
from shapely.wkb import dumps
from shapely.geometry import shape, Polygon

from geotrellis_summary_update.secrets import get_token
from geotrellis_summary_update.exceptions import EmptyResponseException

# environment should be set via environment variable. This can be done when deploying the lambda function.
if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"


S3_CLIENT = boto3.client("s3")
TOKEN: str = get_token(ENV)
PENDING_AOI_NAME = "pending_user_areas"
PENDING_AOI_ANALYSES = {
    "dev": {
        "annualupdate_minimal": {
            "change": "206938be-12d9-47b7-9865-44244bfb64d6",
            "summary": "0eead72d-1ad7-4c0f-93c4-793a07cd2e3d",
        },
        "gladalerts": {
            "daily_alerts": "722d90b2-e989-48ca-ba27-f7a8e236ea44",
            "weekly_alerts": "153a2ba7-cff6-4b06-bd76-279271c4ddea",
            "summary": "28e44bd2-cd13-4587-9259-1ba235a82d28",
        },
    }
}


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


def bucket_suffix() -> str:
    """
    Get environment suffix for bucket
    """
    if ENV is None:
        suffix: str = "-dev"
    elif ENV == "production":
        suffix = ""
    else:
        suffix = f"-{ENV}"

    return suffix


def api_prefix() -> str:
    """
    Get environment prefix for API
    """
    if ENV == "production":
        suffix: str = "production"
    else:
        suffix = f"staging"

    return suffix
