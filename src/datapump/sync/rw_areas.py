import io
import json
import os
import traceback
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

import requests
from requests import Response
from shapely.geometry import MultiPolygon, Polygon, shape
from shapely.wkb import dumps

from ..clients.aws import get_s3_client, get_s3_path, get_s3_path_parts
from ..clients.rw_api import token, update_area_statuses
from ..globals import GLOBALS, LOGGER
from ..util.exceptions import EmptyResponseException, UnexpectedResponseError
from ..util.slack import slack_webhook
from ..util.util import api_prefix

DIRNAME = os.path.dirname(__file__)
GEOSTORE_PAGE_SIZE = 25


def create_1x1_tsv(version: str) -> Optional[str]:
    tsv = get_virtual_1x1_tsv()

    if tsv:
        LOGGER.info("Geostores processed, uploading and analyzing")
        geostore_path = f"geotrellis/features/geostore/{version}.tsv"
        get_s3_client().put_object(
            Body=tsv,
            Bucket=GLOBALS.s3_bucket_pipeline,
            Key=geostore_path,
        )
        return get_s3_path(GLOBALS.s3_bucket_pipeline, geostore_path)
    else:
        LOGGER.info("No geostores to process")
        return None


def get_virtual_1x1_tsv() -> Optional[bytes]:
    """
    Main Lambda function
    """

    LOGGER.info("Check for pending areas")

    try:
        areas: List[Any] = get_pending_areas()
        geostore_ids: List[str] = get_geostore_ids(areas)
        if not geostore_ids:
            raise EmptyResponseException

        geostore: Dict[str, Any] = get_geostore(geostore_ids)
        geostore = filter_geostores(geostore)

        if not geostore:
            raise EmptyResponseException

        with geostore_to_wkb(geostore) as (wkb, geom_count):
            if geom_count == 0:
                raise EmptyResponseException

            return str.encode(wkb.getvalue())
    except EmptyResponseException:
        slack_webhook("INFO", "No new user areas found. Doing nothing.")
        return None
    except Exception:
        LOGGER.error(traceback.format_exc())
        slack_webhook(
            "ERROR", "Error processing new user areas. See logs for more info."
        )
        return None


def get_pending_areas() -> List[Any]:
    """
    Request to GFW API to get list of user areas which were recently submitted and need to be added to nightly updates
    """

    LOGGER.info("Get pending Areas")
    LOGGER.info(f"Using token {token()} for {api_prefix()} API")
    headers: Dict[str, str] = {"Authorization": f"Bearer {token()}"}

    # For some reason we are the only place calling this RW API to sync
    # new subscriptions with areas. See GTC-2987 to fix this workflow.
    yesterday = (datetime.now() - timedelta(1)).strftime("%Y-%m-%d")
    sync_url: str = f"https://{api_prefix()}-api.globalforestwatch.org/v2/area/sync?startDate={yesterday}"
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

    LOGGER.info("Get Geostore IDs")
    geostore_ids: List[str] = list()
    error_ids = list()
    for area in areas:
        if (
            "attributes" in area.keys()
            and "geostore" in area["attributes"].keys()
            and area["attributes"]["geostore"] is not None
        ):
            LOGGER.info(
                f"Found geostore {area['attributes']['geostore']} for area {area['id']} "
            )
            if len(area["attributes"]["geostore"]) != 32:
                error_ids.append(area["attributes"]["geostore"])
            else:
                geostore_ids.append(area["attributes"]["geostore"])
        else:
            LOGGER.warning(f"Cannot find geostore ID for area {area['id']} - skip")

    LOGGER.info(f"IDS: {geostore_ids}")

    if error_ids:
        LOGGER.info(f"Setting invalid geostore IDs to error: {error_ids}")
        update_area_statuses(error_ids, "error")

    # only return unique geostore ids
    # Return max 2000 at a time, otherwise the lambda might time out
    remaining_ids: List[Any] = list(set(geostore_ids) - {None})[:1500]
    return remaining_ids


def get_geostore(geostore_ids: List[str]) -> Dict[str, Any]:
    """
    Get Geostore Geometry using list of geostore IDs
    """

    LOGGER.info("Get Geostore Geometries by IDs")

    headers: Dict[str, str] = {"Authorization": f"Bearer {token()}"}
    url: str = (
        f"https://{api_prefix()}-api.globalforestwatch.org/v2/geostore/find-by-ids"
    )
    geostores: Dict[str, Any] = {"data": []}

    for i in range(0, len(geostore_ids), GEOSTORE_PAGE_SIZE):
        payload: Dict[str, List[str]] = {
            "geostores": geostore_ids[i : i + GEOSTORE_PAGE_SIZE]
        }

        retries = 0
        while retries < 2:
            r: Response = requests.post(url, json=payload, headers=headers)

            if r.status_code != 200:
                retries += 1
                if retries > 1:
                    raise UnexpectedResponseError(
                        f"geostore/find-by-ids returned response {r.status_code} on block {i}"
                    )
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

    update_area_statuses(filtered_geostores, "error")

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

    LOGGER.info("Convert Geometries to WKB")

    extent_1x1: List[Tuple[Polygon, bool, bool]] = _get_extent_1x1()
    wkb: io.StringIO = io.StringIO()

    LOGGER.info("Start writing to virtual TSV file")
    # Column Header
    wkb.write("geostore_id\tgeom\ttcl\tglad\n")
    count: int = 0

    # Body
    try:
        error_ids = []
        for g in geostore["data"]:
            LOGGER.info(f"Processing geostore {g['geostoreId']}")

            try:
                raw_geom = g["geostore"]["data"]["attributes"]["geojson"]["features"][
                    0
                ]["geometry"]

                if raw_geom["type"] != "Polygon" and raw_geom["type"] != "MultiPolygon":
                    LOGGER.warning(f"Invalid geometry type {g['geostoreId']}: {raw_geom['type'] }")
                    error_ids.append(g["geostoreId"])
                    continue

                geom: Polygon = shape(raw_geom)

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
                        error_ids.append(g["geostoreId"]["data"]["id"])
                        continue

                for tile in extent_1x1:
                    if geom.intersects(tile[0]):
                        LOGGER.info(
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

        if error_ids:
            LOGGER.info(f"Setting invalid geostore IDs to error: {error_ids}")
            update_area_statuses(error_ids, "error")

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
    LOGGER.info("Fetch Extent File")
    result_bucket = os.environ["S3_BUCKET_PIPELINE"]
    response: Dict[str, Any] = get_s3_client().get_object(
        Bucket=result_bucket,
        Key="geotrellis/features/extent_1x1.geojson",
    )

    glad_tiles: Dict[str, Any] = json.load(response["Body"])

    extent_1x1: List[Tuple[Polygon, bool, bool]] = list()

    LOGGER.info("Read Extent Features")

    for feature in glad_tiles["features"]:
        geom: Polygon = shape(feature["geometry"])
        extent_1x1.append(
            (geom, feature["properties"]["tcl"], feature["properties"]["glad"])
        )

    return extent_1x1


def get_aoi_geostore_ids(aoi_src: str) -> Set[str]:
    geostore_ids = set()
    aoi_bucket, aoi_key = get_s3_path_parts(aoi_src)

    with io.BytesIO() as data:
        get_s3_client().download_fileobj(aoi_bucket, aoi_key, data)

        rows = data.getvalue().decode("utf-8").split("\n")

    first = True
    for row in rows:
        geostore_id = row.split("\t")[0]
        if first:
            first = False
        elif geostore_id:
            geostore_ids.add(geostore_id)

    return geostore_ids
