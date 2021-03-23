from typing import Dict, Any, List, Optional
from hashlib import blake2b
import os
import json

import boto3
from boto3.dynamodb.conditions import Attr, And
from pydantic import BaseModel
from botocore.exceptions import ClientError

from ..clients.aws import get_s3_path_parts
from ..globals import LOGGER, GLOBALS

# Key - had of analysis_analysis_version_dataset_dataset_version

class DatapumpConfig(BaseModel):
    analysis_version: str
    dataset: str
    dataset_version: str
    analysis: str
    sync: bool
    sync_type: str
    sync_version: Optional[str] = None
    metadata: Dict[str, Any] = {}

    def get_id(self):
        id_str = f"{self.analysis}_{self.analysis_version}_{self.dataset}_{self.dataset_version}"
        id_hash = blake2b(id_str.encode(), digest_size=10).hexdigest()
        return id_hash


class DatapumpStore:
    def __init__(self):
        # use table resource API since it makes putting items much easier
        dynamodb = boto3.resource('dynamodb', endpoint_url=GLOBALS.aws_endpoint_uri)
        self._client = dynamodb.Table(GLOBALS.dynamodb_table_name)

    def put(
        self, config_row: DatapumpConfig
    ) -> None:
        # query for hash
        attributes = config_row.dict()
        attributes["id"] = config_row.get_id()

        self._client.put_item(Item=attributes)

    def remove(
        self, config_row: DatapumpConfig
    ):
        self._client.delete_item(Key={
            'id': config_row.get_id()
        })

    def get(self, **kwargs) -> List[DatapumpConfig]:
        filter_expr = And(*[Attr(key).eq(value) for key, value in kwargs.items])
        response = self._client.scan(FilterExpression=filter_expr)
        items = response["Items"]

        return [
            DatapumpConfig(**item for item in items)
        ]