import requests

from datapump_utils.globals import DATA_API_URI


class DataApiClient:
    def get_latest(self):
        pass

    def get_assets(self, dataset: str, version: str):
        return requests.get(f"{DATA_API_URI}/{dataset}/{version}/assets").json()["data"]

    def get_1x1_asset(self, dataset: str, version: str) -> str:
        assets = self.get_assets(dataset, version)

        for asset in assets:
            if asset["asset_type"] == "1x1 grid":
                return asset["asset_uri"]

    def create_new_version(self, source_uri):
        pass

    def append(self):
        pass
