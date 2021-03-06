import io
import json
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Iterator, List, Tuple, Set
import math
import traceback

import requests
from requests import Response
from shapely.wkb import dumps
from shapely.geometry import shape, Polygon, MultiPolygon
from datapump_utils.exceptions import EmptyResponseException, UnexpectedResponseError
from datapump_utils.logger import get_logger
from datapump_utils.secrets import token
from datapump_utils.util import bucket_suffix, api_prefix
from datapump_utils.s3 import get_s3_path, s3_client
from datapump_utils.slack import slack_webhook
from datapump_utils.dataset import update_aoi_statuses


# environment should be set via environment variable. This can be done when deploying the lambda function.
if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"

LOGGER = get_logger(__name__)
SUMMARIZE_NEW_AOIS_NAME = "new-user-areas"
DIRNAME = os.path.dirname(__file__)
DATASETS = json.loads(os.environ["DATASETS"]) if "DATASETS" in os.environ else dict()
GEOSTORE_PAGE_SIZE = 100


def handler(event: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main Lambda function
    """

    LOGGER.info("Check for pending areas")

    now: datetime = datetime.now()

    try:
        areas: List[Any] = get_pending_areas()
        geostore_ids: List[str] = get_geostore_ids(areas)
        if geostore_ids:
            geostore: Dict[str, Any] = get_geostore(geostore_ids)
            geostore = filter_geostores(geostore)

            if geostore:
                geostore_path = f"geotrellis/features/geostore/aoi-{now.strftime('%Y%m%d_%H%M')}.tsv"
                geostore_bucket = f"gfw-pipelines{bucket_suffix()}"

                with geostore_to_wkb(geostore) as (wkb, geom_count):
                    if geom_count == 0:
                        slack_webhook("INFO", "No new user areas found. Doing nothing.")
                        return {"status": "NO_NEW_AREAS_FOUND"}

                    s3_client().put_object(
                        Body=str.encode(wkb.getvalue()),
                        Bucket=geostore_bucket,
                        Key=geostore_path,
                    )
                    worker_count = max(25, math.ceil(geom_count / 100))

                LOGGER.info(f"Found {len(geostore['data'])} pending areas")
                geostore_full_path = get_s3_path(geostore_bucket, geostore_path)

                # heuristic for how many workers we'll need to process this in Spark/EMR

                return {
                    "status": "NEW_AREAS_FOUND",
                    "instance_size": "r4.2xlarge",
                    "instance_count": worker_count,
                    "feature_src": geostore_full_path,
                    "feature_type": "geostore",
                    "analyses": ["gladalerts", "annualupdate_minimal", "firealerts"],
                    "datasets": DATASETS["geostore"],
                    "name": SUMMARIZE_NEW_AOIS_NAME,
                    "upload_type": "append",
                    "get_summary": True,
                    "fire_config": {
                        "viirs": [
                            "s3://gfw-data-lake/nasa_viirs_fire_alerts/v1/vector/epsg-4326/tsv/near_real_time/*.tsv",
                            "s3://gfw-data-lake/nasa_viirs_fire_alerts/v1/vector/epsg-4326/tsv/scientific/*.tsv",
                        ],
                        "modis": [
                            "s3://gfw-data-lake/nasa_modis_fire_alerts/v6/vector/epsg-4326/tsv/near_real_time/*.tsv",
                            "s3://gfw-data-lake/nasa_modis_fire_alerts/v6/vector/epsg-4326/tsv/scientific/*.tsv",
                        ],
                    },
                }
            else:
                slack_webhook("INFO", "No new user areas found. Doing nothing.")
                return {"status": "NO_NEW_AREAS_FOUND"}
        else:
            slack_webhook("INFO", "No new user areas found. Doing nothing.")
            return {"status": "NO_NEW_AREAS_FOUND"}
    except EmptyResponseException:
        slack_webhook("INFO", "No new user areas found. Doing nothing.")
        return {"status": "NO_NEW_AREAS_FOUND"}
    except Exception as e:
        LOGGER.error(traceback.format_exc())
        slack_webhook(
            "ERROR", "Error processing new user areas. See logs for more info."
        )
        return {"status": "ERROR", "message": str(e)}


def get_pending_areas() -> List[Any]:
    """
    Request to GFW API to get list of user areas which were recently submitted and need to be added to nightly updates
    """

    LOGGER.debug("Get pending Areas")
    LOGGER.debug(f"Using token {token()} for {api_prefix()} API")
    headers: Dict[str, str] = {"Authorization": f"Bearer {token()}"}

    # Area sync
    sync_url: str = f"https://{api_prefix()}-api.globalforestwatch.org/v2/area/sync"
    sync_resp = requests.post(sync_url, headers=headers)

    if sync_resp.status_code != 200:
        raise Exception(
            f"v2/area/sync API failed with status code {sync_resp.status_code}, can't process areas"
        )

    pending_areas: List[Any] = []
    has_next_page = True
    page_size = GEOSTORE_PAGE_SIZE
    page_number = 1

    while has_next_page:
        url: str = f"http://{api_prefix()}-api.globalforestwatch.org/v2/area?status=pending&all=true&page[number]={page_number}&page[size]={page_size}"
        r: Response = requests.get(url, headers=headers)

        if r.status_code != 200:
            raise UnexpectedResponseError(
                f"Get areas returned response {r.status_code} on page number {page_number}"
            )

        page_areas = r.json()
        page_number += 1
        pending_areas += page_areas["data"]
        has_next_page = page_areas["links"]["self"] != page_areas["links"]["last"]

    return pending_areas


def get_geostore_ids(areas: List[Any]) -> List[str]:
    """
    Extract Geostore ID from user area
    """

    LOGGER.debug("Get Geostore IDs")
    geostore_ids: List[str] = list()
    for area in areas:
        if "attributes" in area.keys() and "geostore" in area["attributes"].keys():
            LOGGER.debug(
                f"Found geostore {area['attributes']['geostore']} for area {area['id']} "
            )
            geostore_ids.append(area["attributes"]["geostore"])
        else:
            LOGGER.warning(f"Cannot find geostore ID for area {area['id']} - skip")

    LOGGER.debug(f"IDS: {geostore_ids}")

    # only return unique geostore ids
    # Return max 2000 at a time, otherwise the lambda might time out
    return list(set(geostore_ids))[:1500]


def get_geostore(geostore_ids: List[str]) -> Dict[str, Any]:
    """
    Get Geostore Geometry using list of geostore IDs
    """

    LOGGER.debug("Get Geostore Geometries by IDs")

    headers: Dict[str, str] = {"Authorization": f"Bearer {token()}"}
    url: str = f"https://{api_prefix()}-api.globalforestwatch.org/v2/geostore/find-by-ids"
    geostores: Dict[str, Any] = {"data": []}

    for i in range(0, len(geostore_ids), GEOSTORE_PAGE_SIZE):
        payload: Dict[str, List[str]] = {
            "geostores": geostore_ids[i : i + GEOSTORE_PAGE_SIZE]
        }

        retries = 0
        while retries < 2:
            r: Response = requests.post(url, json=payload, headers=headers)

            if r.status_code != 200:
                if retries > 1:
                    raise UnexpectedResponseError(
                        f"geostore/find-by-ids returned response {r.status_code} on block {i}"
                    )
                else:
                    retries += 1
            else:
                geostores["data"] += r.json()["data"]
                break

    return geostores


def filter_geostores(geostores: Dict[str, Any]) -> Dict[str, Any]:
    filtered_geostores: Set[Any] = set()

    filtered_geostores = filtered_geostores.union(
        set(
            [
                g["geostoreId"]
                for g in geostores["data"]
                if g["geostore"]["data"]["attributes"]["areaHa"] >= 1_000_000_000
            ]
        )
    )

    filtered_geostores = filtered_geostores.union(
        set(
            [
                g["geostoreId"]
                for g in geostores["data"]
                if not g["geostore"]["data"]["attributes"]["geojson"]["features"]
                or not g["geostore"]["data"]["attributes"]["geojson"]["features"][0][
                    "geometry"
                ]["coordinates"]
            ]
        )
    )

    update_aoi_statuses(filtered_geostores, "error")

    all_geostore_ids: Set[Any] = set([g["geostoreId"] for g in geostores["data"]])
    remaining_geostore_ids: List[Any] = list(
        all_geostore_ids.difference(filtered_geostores)
    )

    remaining_geostores = [
        g for g in geostores["data"] if g["geostoreId"] in remaining_geostore_ids
    ]
    return {"data": remaining_geostores}


@contextmanager
def geostore_to_wkb(geostore: Dict[str, Any]) -> Iterator[Tuple[io.StringIO, int]]:
    """
    Convert Geojson to WKB. Slice geometries into 1x1 degree tiles
    """

    LOGGER.debug("Convert Geometries to WKB")

    extent_1x1: List[Tuple[Polygon, bool, bool]] = _get_extent_1x1()
    wkb: io.StringIO = io.StringIO()

    LOGGER.debug("Start writing to virtual TSV file")
    # Column Header
    wkb.write(f"geostore_id\tgeom\ttcl\tglad\n")
    count: int = 0

    # Body
    try:
        for g in geostore["data"]:
            try:
                geom: Polygon = shape(
                    g["geostore"]["data"]["attributes"]["geojson"]["features"][0][
                        "geometry"
                    ]
                )

                # dilate geometry to remove any slivers or other possible small artifacts that might cause issues
                # in geotrellis
                # https://gis.stackexchange.com/questions/120286/removing-small-polygon-gaps-in-shapely-polygon
                geom = geom.buffer(0.0001).buffer(-0.0001)

                # if GEOS thinks geom is invalid, try calling buffer(0) to rewrite it without changing the geometry
                if not geom.is_valid:
                    geom = geom.buffer(0)
                    if (
                        not geom.is_valid
                    ):  # is still invalid, we'll need to look into this, but skip for now
                        LOGGER.warning(
                            f"Invalid geometry {g['geostoreId']}: {geom.wkt}"
                        )
                        continue

                for tile in extent_1x1:
                    if geom.intersects(tile[0]):
                        LOGGER.debug(
                            f"Feature {g['geostoreId']} intersects with bounds {tile[0].bounds} -> add to WKB"
                        )
                        intersecting_polygon = _get_intersecting_polygon(geom, tile[0])

                        if intersecting_polygon:
                            wkb.write(
                                f"{g['geostoreId']}\t{dumps(intersecting_polygon, hex=True)}\t{tile[1]}\t{tile[2]}\n"
                            )
                            count += 1
            except Exception as e:
                LOGGER.error(f"Error processing geostore {g['geostoreId']}")
                raise e

        yield (wkb, count)

    finally:
        wkb.close()


def _get_intersecting_polygon(feature_geom, tile_geom):
    """
    Get intersection of feature and tile, and ensure the result is either a Polygon or MultiPolygon,
    or returns None if the intersection contains no polygons.
    """

    intersection = feature_geom.intersection(tile_geom)

    if intersection.type == "Polygon" or intersection.type == "MultiPolygon":
        return intersection
    elif intersection.type == "GeometryCollection":
        polygons = [geom for geom in intersection.geoms if geom.type == "Polygon"]

        if len(polygons) == 1:
            return polygons[0]
        elif len(polygons) > 1:
            return MultiPolygon(polygons)
        else:
            return None
    else:
        return None


def _get_extent_1x1() -> List[Tuple[Polygon, bool, bool]]:
    """
    Fetch 1x1 degree extent file
    """
    LOGGER.debug("Fetch Extent File")
    result_bucket = os.environ["S3_BUCKET_PIPELINE"]
    response: Dict[str, Any] = s3_client().get_object(
        Bucket=result_bucket, Key="geotrellis/features/extent_1x1.geojson",
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
