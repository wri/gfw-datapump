import io
import json
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Iterator, List, Tuple

import boto3
import requests
import yaml
from requests import Response
from shapely.wkb import dumps
from shapely.geometry import shape, Polygon

from geotrellis_summary_update.decorators import api_response_checker
from geotrellis_summary_update.exceptions import (
    EmptyResponseException,
    UnexpectedResponseError,
)
from geotrellis_summary_update.logger import get_logger
from geotrellis_summary_update.secrets import get_token
from geotrellis_summary_update.util import bucket_suffix, api_prefix


# environment should be set via environment variable. This can be done when deploying the lambda function.
if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"


LOGGER = get_logger(__name__)
S3_CLIENT = boto3.client("s3")
TOKEN: str = get_token()
PENDING_AOI_NAME = "pending_user_areas"

DIRNAME = os.path.dirname(__file__)

with open(os.path.join(DIRNAME, "analysis_config.yaml"), "r") as config:
    PENDING_AOI_ANALYSES = yaml.safe_load(config)


def handler(event: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main Lambda function
    """

    LOGGER.info("Check for pending areas")

    now: datetime = datetime.now()

    try:
        areas: Dict[str, Any] = get_pending_areas()
        geostore_ids: List[str] = get_geostore_ids(areas)
        geostore: Dict[str, Any] = get_geostore(geostore_ids)
        geostore_path = f"geotrellis/features/geostore/aoi-{now.strftime('%Y%m%d')}.tsv"

        with geostore_to_wkb(geostore) as wkb:
            S3_CLIENT.put_object(
                Body=str.encode(wkb.getvalue()),
                Bucket=f"gfw-pipelines{bucket_suffix()}",
                Key=geostore_path,
            )

        LOGGER.info(f"Found {len(geostore['data'])} pending areas")
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
    except Exception as e:
        return {"status": "FAILED", "message": e}


@api_response_checker("pending areas")
def get_pending_areas() -> Dict[str, Any]:
    """
    Request to GFW API to get list of user areas which were recently submitted and need to be added to nightly updates
    """

    LOGGER.debug("Get pending Areas")
    LOGGER.debug(f"Using token {TOKEN} for {api_prefix()} API")
    headers: Dict[str, str] = {"Authorization": f"Bearer {TOKEN}"}
    url: str = f"http://{api_prefix()}-api.globalforestwatch.org/v2/area?status=pending&all=true"
    r: Response = requests.get(url, headers=headers)

    return r.json()


def get_geostore_ids(areas: Dict[str, Any]) -> List[str]:
    """
    Extract Geostore ID from user area
    """

    LOGGER.debug("Get Geostore IDs")
    geostore_ids: List[str] = list()
    for area in areas["data"]:
        if "attributes" in area.keys() and "geostore" in area["attributes"].keys():
            LOGGER.debug(
                f"Found geostore {area['attributes']['geostore']} for area {area['id']} "
            )
            geostore_ids.append(area["attributes"]["geostore"])
        else:
            LOGGER.warning(f"Cannot find geostore ID for area {area['id']} - skip")

    LOGGER.debug(f"IDS: {geostore_ids}")

    return geostore_ids


@api_response_checker(endpoint="geostores")
def get_geostore(geostore_ids: List[str]) -> Dict[str, Any]:
    """
    Get Geostore Geometry using list of geostore IDs
    """

    LOGGER.debug("Get Geostore Geometries by IDs")

    headers: Dict[str, str] = {"Authorization": f"Bearer {TOKEN}"}
    payload: Dict[str, List[str]] = {"geostores": geostore_ids}
    url: str = f"https://{api_prefix()}-api.globalforestwatch.org/v2/geostore/find-by-ids"
    r: Response = requests.post(url, data=payload, headers=headers)

    return r.json()


@contextmanager
def geostore_to_wkb(geostore: Dict[str, Any]) -> Iterator[io.StringIO]:
    """
    Convert Geojson to WKB. Slice geometries into 1x1 degree tiles
    """

    LOGGER.debug("Convert Geometries to WKB")

    extent_1x1: List[Tuple[Polygon, bool, bool]] = _get_extent_1x1()
    wkb = io.StringIO()

    LOGGER.debug("Start writing to virtual TSV file")
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
                    LOGGER.debug(
                        f"Feature {g['geostoreId']} intersects with bounds {tile[0].bounds} -> add to WKB"
                    )
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
    LOGGER.debug("Fetch Extent File")
    response: Dict[str, Any] = S3_CLIENT.get_object(
        Bucket=f"gfw-data-lake{bucket_suffix()}",
        Key="analysis_extent/latest/vector/extent_1x1.geojson",
    )

    glad_tiles: Dict[str, Any] = json.load(response["Body"])

    extent_1x1: List[Tuple[Polygon, bool, bool]] = list()

    LOGGER.debug("Read Extent Features")

    for feature in glad_tiles["features"]:
        geom: Polygon = shape(feature["geometry"])
        extent_1x1.append(
            (geom, feature["properties"]["tcl"], feature["properties"]["glad"])
        )

    return extent_1x1
