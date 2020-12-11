import requests
from typing import List, Dict, Any
from pprint import pformat

from ..globals import DATA_API_URI, LOGGER
from ..util.exceptions import DataApiResponseError
from .rw_api import token


class DataApiClient:
    def get_latest(self):
        pass

    def get_assets(self, dataset: str, version: str) -> List[Dict[str, Any]]:
        uri = f"{DATA_API_URI}/{dataset}/{version}/assets"
        return requests.get(uri).json()["data"]

    def get_1x1_asset(self, dataset: str, version: str) -> str:
        assets = self.get_assets(dataset, version)

        for asset in assets:
            if asset["asset_type"] == "1x1 grid":
                return asset["asset_uri"]

        raise ValueError(f"Dataset {dataset}/{version} missing 1x1 grid asset")

    def add_version(
        self,
        dataset: str,
        version: str,
        source_uris: List[str],
        indices: List[str],
        cluster: List[str],
    ) -> Dict[str, Any]:
        payload = {
            "creation_options": {
                "source_type": "table",
                "source_driver": "text",
                "source_uri": source_uris,
                "delimiter": "\t",
                "has_header": True,
                "indices": [{"index_type": "btree", "column_names": indices}],
                "cluster": {"index_type": "btree", "column_names": cluster},
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token()}",
        }

        uri = f"{DATA_API_URI}/{dataset}/{version}"

        LOGGER.debug(f"Adding new version at {uri} with payload:\n{pformat(payload)}")
        resp = requests.put(uri, json=payload, headers=headers)

        if resp.status_code >= 300:
            raise DataApiResponseError(
                f"Data API responded with status code {resp.status_code}"
            )
        else:
            return resp.json()["data"]

    def append(self, dataset: str, version: str, source_uris: List[str]):
        payload = {"creation_options": {"source_uri": source_uris}}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token()}",
        }

        uri = f"{DATA_API_URI}/{dataset}/{version}/append"

        LOGGER.debug(f"Appending to version at {uri} with payload:\n{pformat(payload)}")
        resp = requests.post(uri, json=payload, headers=headers)

        if resp.status_code >= 300:
            raise DataApiResponseError(
                f"Data API responded with status code {resp.status_code}"
            )
        else:
            return resp.json()["data"]

    def get_version(self, dataset: str, version: str):
        resp = requests.get(f"{DATA_API_URI}/{dataset}/{version}")

        if resp.status_code >= 300:
            raise DataApiResponseError(
                f"Data API responded with status code {resp.status_code}"
            )
        else:
            return resp.json()["data"]
