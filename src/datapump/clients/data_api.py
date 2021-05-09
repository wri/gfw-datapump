import json
from enum import Enum
from pprint import pformat
from typing import Any, Dict, List, Optional

import requests

from ..globals import GLOBALS, LOGGER
from ..util.exceptions import DataApiResponseError
from .rw_api import token


class ValidMethods(str, Enum):
    post = "POST"
    put = "PUT"
    patch = "PATCH"
    get = "GET"
    delete = "DELETE"


class DataApiClient:
    def __init__(self):
        LOGGER.info(f"Create data API client at URI: {GLOBALS.data_api_uri}")

    def get_latest_version(self, dataset: str) -> str:
        uri = f"{GLOBALS.data_api_uri}/dataset/{dataset}/latest"
        resp = self._send_request(ValidMethods.get, uri)
        if resp["status"] == "success":
            return resp["data"]["version"]
        else:
            raise ValueError(f"No latest version set for dataset {dataset}")

    def get_assets(self, dataset: str, version: str) -> List[Dict[str, Any]]:
        uri = f"{GLOBALS.data_api_uri}/dataset/{dataset}/{version}/assets"
        return self._send_request(ValidMethods.get, uri)["data"]

    def get_asset(self, dataset: str, version: str, asset_type: str):
        assets = self.get_assets(dataset, version)

        for asset in assets:
            if asset["asset_type"] == asset_type:
                return asset

        raise ValueError(f"Dataset {dataset}/{version} missing {asset_type} asset")

    def get_1x1_asset(self, dataset: str, version: str) -> str:
        # geostore and gadm are special
        if dataset == "geostore":
            return (
                f"s3://{GLOBALS.s3_bucket_pipeline}/geotrellis/features/geostore/*.tsv"
            )
        elif dataset == "gadm" and version == "v3.6":
            return "s3://gfw-files/2018_update/tsv/gadm36_adm2_1_1.csv"

        return self.get_asset(dataset, version, "1x1 grid")["asset_uri"]

    def create_dataset_and_version(
        self,
        dataset: str,
        version: str,
        source_uris: List[str],
        indices: List[Dict[str, Any]],
        cluster: Dict[str, Any],
        table_schema: List[Dict[str, Any]],
        partitions: Optional[Dict[str, Any]] = None,
        latitude_field: Optional[str] = None,
        longitude_field: Optional[str] = None,
        metadata: Dict[str, Any] = {},
    ) -> Dict[str, Any]:
        try:
            self.get_dataset(dataset)
        except DataApiResponseError:
            self.create_dataset(dataset, metadata)

        return self.create_version(
            dataset,
            version,
            source_uris,
            indices,
            cluster,
            table_schema,
            partitions,
            latitude_field,
            longitude_field,
        )

    def create_dataset(
        self, dataset: str, metadata: Dict[str, Any] = {}
    ) -> Dict[str, Any]:
        uri = f"{GLOBALS.data_api_uri}/dataset/{dataset}"
        payload = {"metadata": metadata}

        return self._send_request(ValidMethods.put, uri, payload)["data"]

    def create_version(
        self,
        dataset: str,
        version: str,
        source_uris: List[str],
        indices: List[Dict[str, Any]],
        cluster: Dict[str, Any],
        table_schema: List[Dict[str, Any]],
        partitions: Optional[Dict[str, Any]] = None,
        latitude_field: Optional[str] = None,
        longitude_field: Optional[str] = None,
    ) -> Dict[str, Any]:
        creation_options = {
            "source_type": "table",
            "source_driver": "text",
            "source_uri": source_uris,
            "delimiter": "\t",
            "has_header": True,
            "indices": indices,
            "cluster": cluster,
            "table_schema": table_schema,
        }

        if partitions:
            creation_options["partitions"] = partitions
        if latitude_field and longitude_field:
            creation_options["latitude"] = latitude_field
            creation_options["longitude"] = longitude_field

        payload = {"creation_options": creation_options}

        uri = f"{GLOBALS.data_api_uri}/dataset/{dataset}/{version}"
        return self._send_request(ValidMethods.put, uri, payload)["data"]

    def create_raster_version(
        self,
        dataset: str,
        version: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:

        uri = f"{GLOBALS.data_api_uri}/dataset/{dataset}/{version}"
        return self._send_request(ValidMethods.put, uri, payload)["data"]

    def create_aux_asset(
        self,
        dataset: str,
        version: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:

        uri = f"{GLOBALS.data_api_uri}/dataset/{dataset}/{version}/assets"
        return self._send_request(ValidMethods.post, uri, payload)["data"]


    def append(
        self, dataset: str, version: str, source_uris: List[str]
    ) -> Dict[str, Any]:
        payload = {"source_uri": source_uris}
        uri = f"{GLOBALS.data_api_uri}/dataset/{dataset}/{version}/append"
        return self._send_request(ValidMethods.post, uri, payload)["data"]

    def copy_version(
        self, dataset: str, old_version: str, new_version: str, source_uris: List[str]
    ):
        table_asset = self.get_asset(dataset, old_version, "Database table")
        creation_options_uri = (
            f"{GLOBALS.data_api_uri}/asset/{table_asset['asset_id']}/creation_options"
        )
        creation_options = self._send_request(ValidMethods.get, creation_options_uri)[
            "data"
        ]

        return self.create_version(
            dataset,
            new_version,
            source_uris,
            creation_options["indices"],
            creation_options["cluster"],
            creation_options["table_schema"],
            creation_options["partitions"],
            creation_options["latitude"],
            creation_options["longitude"],
        )

    def get_version(self, dataset: str, version: str) -> Dict[str, Any]:
        uri = f"{GLOBALS.data_api_uri}/dataset/{dataset}/{version}"
        return self._send_request(ValidMethods.get, uri)["data"]

    def get_dataset(self, dataset: str) -> Dict[str, Any]:
        uri = f"{GLOBALS.data_api_uri}/dataset/{dataset}"
        return self._send_request(ValidMethods.get, uri)["data"]

    def get_datasets(self) -> List[Dict[str, Any]]:
        uri = f"{GLOBALS.data_api_uri}/datasets"
        return self._send_request(ValidMethods.get, uri)["data"]

    def delete_version(self, dataset: str, version: str) -> None:
        uri = f"{GLOBALS.data_api_uri}/dataset/{dataset}/{version}"
        self._send_request(ValidMethods.delete, uri)

    def set_latest(self, dataset: str, version: str):
        uri = f"{GLOBALS.data_api_uri}/dataset/{dataset}/{version}"
        payload = {"is_latest": True}
        self._send_request(ValidMethods.patch, uri, payload)

    @staticmethod
    def _send_request(
        method: ValidMethods, uri: str, payload: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        LOGGER.info(
            f"Send Data API request:\n"
            f"\tURI: {uri}\n"
            f"\tMethod: {method.value}\n"
            f"\tPayload:{json.dumps(payload)}\n"
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token()}",
        }

        if method == ValidMethods.post:
            resp = requests.post(uri, json=payload, headers=headers)
        elif method == ValidMethods.put:
            resp = requests.put(uri, json=payload, headers=headers)
        elif method == ValidMethods.patch:
            resp = requests.patch(uri, json=payload, headers=headers)
        elif method == ValidMethods.get:
            resp = requests.get(uri, headers=headers)
        elif method == ValidMethods.delete:
            resp = requests.delete(uri, headers=headers)

        if resp.status_code >= 300:
            error_msg = f"Data API responded with status code {resp.status_code}\n"
            try:
                body = resp.json()
                error_msg += pformat(body)
            except Exception:
                error_msg += resp.content.decode()
            finally:
                raise DataApiResponseError(error_msg)
        else:
            return resp.json()
