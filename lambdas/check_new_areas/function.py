import io
import json
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional

import boto3
import requests
from requests import Response
from shapely.wkb import dumps
from shapely.geometry import shape, Polygon

# environment should be set via environment variable. This can be done when deploying the lambda function.
if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"


class EmptyResponseException(Exception):
    pass


def secret_suffix() -> str:
    if ENV == "production":
        suffix: str = "prod"
    else:
        suffix = "staging"
    return suffix


S3_CLIENT = boto3.client("s3")
SM_CLIENT = boto3.client("secretsmanager")
TOKEN: str = SM_CLIENT.get_secret_value(SecretId=f"gfw-api/{secret_suffix()}-token")


def handler(event, context) -> Optional[Dict[str, Any]]:

    now: datetime = datetime.now()

    try:
        areas: Dict[str, Any] = get_pending_areas()
        geostore_ids: List[str] = get_geostore_ids(areas)
        geostore: Dict[str, Any] = get_geostore(geostore_ids)

        with geostore_to_wkb(geostore) as wkb:
            S3_CLIENT.upload_fileobj(
                wkb,
                f"gfw-pipelines{bucket_suffix()}",
                f"geotrellis/features/geostore/aoi-{now.strftime('%Y%m%d')}.tsv",
            )

        return {"status": "FOUND_NEW"}.update(event)
    except EmptyResponseException:
        # slack_webhook("INFO", "No new user areas found. Doing nothing.")
        return {"status": "NOTHING_TO_DO"}
    except Exception:
        return {"status": "FAILED"}


def get_pending_areas() -> Dict[str, Any]:
    headers: Dict[str, str] = {"Authorization": f"Bearer {TOKEN}"}
    url: str = f"http://{api_prefix()}-api.globalforestwatch.org/v2/area?status=pending&all=true"
    r: Response = requests.get(url, headers=headers)

    if not r.json():
        raise EmptyResponseException("No pending areas")
    else:
        return r.json()


def get_geostore_ids(areas: Dict[str, Any]) -> List[str]:

    geostore_ids: List[str] = list()
    for area in areas["data"]:
        geostore_ids.append(area["attributes"]["geostore"])
    return geostore_ids


def get_geostore(geostore_ids: List[str]) -> Dict[str, Any]:
    headers: Dict[str, str] = {"Authorization": f"Bearer {TOKEN}"}
    url: str = f"https://{api_prefix()}-api.globalforestwatch.org/v1/geostore/find-by-ids"
    r: Response = requests.post(url, data=json.dumps(geostore_ids), headers=headers)
    return r.json()


@contextmanager
def geostore_to_wkb(geostore: Dict[str, Any]) -> Iterator[io.StringIO]:
    glad_tiles: List[Polygon] = _get_glad_extent()
    wkb = io.StringIO()
    for g in geostore["data"]:
        geom: Polygon = shape(
            g["geostore"]["data"]["attributes"]["geojson"]["features"][0]["geometry"]
        )
        for tile in glad_tiles:
            intersection = geom.intersection(tile)
            if intersection.area:

                wkb.write(f"{g['geostoreId']}\t{dumps(intersection, hex=True)}\n")
    yield wkb


def _get_glad_extent() -> List[Polygon]:
    response: Dict[str, Any] = S3_CLIENT.get_object(
        Bucket=f"gfw-data-lake{bucket_suffix()}",
        Key="umd_glad_alerts/latest/vector/umd_glad_alerts__extent_1x1.geojson",
    )

    glad_tiles: Dict[str, Any] = json.load(response["Body"])

    glad_extent: List[Polygon] = list()

    for feature in glad_tiles["features"]:
        geom: Polygon = shape(feature["geometry"])
        glad_extent.append(geom)

    return glad_extent


def bucket_suffix() -> str:
    if ENV is None:
        suffix: str = "-dev"
    elif ENV == "production":
        suffix = ""
    else:
        suffix = f"-{ENV}"

    return suffix


def api_prefix() -> str:
    if ENV == "production":
        suffix: str = "production"
    else:
        suffix = f"staging"

    return suffix
