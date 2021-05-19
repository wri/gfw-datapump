from hashlib import blake2b
from typing import Any, Dict, List

import boto3
from boto3.dynamodb.conditions import And, Attr
from pydantic import BaseModel

from ..globals import GLOBALS


class DatapumpConfig(BaseModel):
    analysis_version: str
    dataset: str
    dataset_version: str
    analysis: str
    sync: bool
    sync_type: str
    sync_version: str = ""
    metadata: Dict[str, Any] = {}

    def get_id(self):
        id_str = f"{self.analysis}_{self.analysis_version}_{self.dataset}_{self.dataset_version}_{self.sync_type}"
        id_hash = blake2b(id_str.encode(), digest_size=10).hexdigest()
        return id_hash


class DatapumpStore:
    def __init__(self):
        # use table resource API since it makes putting items much easier
        dynamodb = boto3.resource("dynamodb", endpoint_url=GLOBALS.aws_endpoint_uri)
        self._client = dynamodb.Table(GLOBALS.datapump_table_name)

    def put(self, config_row: DatapumpConfig) -> None:
        # query for hash
        attributes = config_row.dict()
        attributes["id"] = config_row.get_id()

        self._client.put_item(Item=attributes)

    def update_sync_version(
        self, config_row: DatapumpConfig, sync_version: str
    ) -> None:
        self._client.update_item(
            Key={"id": config_row.get_id()},
            UpdateExpression="SET sync_version = :sync_version",
            ExpressionAttributeValues={":sync_version": sync_version},
        )

    def remove(self, config_row: DatapumpConfig):
        self._client.delete_item(Key={"id": config_row.get_id()})

    def get(self, **kwargs) -> List[DatapumpConfig]:
        filter_expr = And(*[Attr(key).eq(value) for key, value in kwargs.items()])
        response = self._client.scan(FilterExpression=filter_expr)
        items = response["Items"]

        return [DatapumpConfig(**item) for item in items]
