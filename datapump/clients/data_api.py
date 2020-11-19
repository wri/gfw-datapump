import requests
from typing import List

from datapump.globals import DATA_API_URI
from datapump.util.exceptions import DataApiResponseError


class DataApiClient:
    def get_latest(self):
        pass

    def get_assets(self, dataset: str, version: str):
        uri = f"{DATA_API_URI}/{dataset}/{version}/assets"
        return requests.get(uri).json()["data"]

    def get_1x1_asset(self, dataset: str, version: str) -> str:
        assets = self.get_assets(dataset, version)

        for asset in assets:
            if asset["asset_type"] == "1x1 grid":
                return asset["asset_uri"]

    def add_version(
        self, dataset: str, version: str, source_uris: List[str], indices, cluster
    ):
        payload = {
            "creation_options": {
                "source_type": "table",
                "source_driver": "text",
                "source_uri": source_uris,
                "delimiter": "\t",
                "table_schema": "",
                "indices": indices,
                "cluster": cluster,
            }
        }

        resp = requests.put(f"{DATA_API_URI}/{dataset}/{version}", json=payload)

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

    def append(self):
        pass
