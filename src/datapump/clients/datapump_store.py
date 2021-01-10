from typing import Dict, Any, List
import os
import json

from pydantic import BaseModel
import sqlite3
from botocore.exceptions import ClientError

from ..clients.aws import get_s3_client, get_s3_path_parts
from ..globals import LOGGER

DB_PATH = os.environ["DATAPUMP_DB_S3_PATH"]
DB_BUCKET, DB_KEY = get_s3_path_parts(DB_PATH)
LOCAL_DB_PATH = "/tmp/datapump.db"


class DatapumpConfig(BaseModel):
    analysis_version: str
    dataset: str
    dataset_version: str
    analysis: str
    sync: bool
    sync_type: str
    metadata: Dict[str, Any] = {}


class DatapumpStore:
    def __init__(self):
        self.conn = None

    def __enter__(self):
        try:
            get_s3_client().download_file(DB_BUCKET, DB_KEY, LOCAL_DB_PATH)
            self.conn = sqlite3.connect(LOCAL_DB_PATH)
        except ClientError:
            LOGGER.info("Unable to find config db, creating new one.")
            self.conn = sqlite3.connect(LOCAL_DB_PATH)

            create_sql = """
            CREATE TABLE datapump (
                analysis_version varchar(255),
                dataset varchar(255),
                dataset_version varchar(255),
                analysis varchar(255),
                sync boolean,
                sync_type varchar(255),
                metadata json
            )
            """
            self.conn.execute(create_sql)
            self.conn.commit()

        return self

    def add(
        self, config_row: DatapumpConfig
    ) -> None:  # analysis_version: str, dataset: str, dataset_version: str, analysis: str, sync: bool, metadata: Dict[str, Any] = {}
        """
        Create entries for each table in new version
        :param version: New version
        :param tables: List of all tables to include in version
        :return: None
        """

        # check if entry already exists
        existing_row = self.get(**config_row.dict())
        if existing_row:
            LOGGER.debug(f"Row already exists, skipping write: {existing_row}")
            return

        row_values = [
            str(val).lower() if key != "metadata" else json.dumps(val)
            for key, val in config_row.dict().items()
        ]

        self.conn.execute("INSERT INTO datapump VALUES(?,?,?,?,?,?,?)", row_values)
        self.conn.commit()

    def get(self, **kwargs) -> List[DatapumpConfig]:
        sql = "SELECT * FROM datapump"

        if kwargs:
            sql += " WHERE " + " AND ".join(
                f"{k} = '{v}'" for k, v in kwargs.items() if k != "metadata"
            )

        LOGGER.debug(f"Executing select query: {sql}")
        cursor = self.conn.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        return [
            DatapumpConfig(
                **dict(
                    [
                        (col, row_val)
                        if col != "metadata"
                        else (col, json.loads(row_val))
                        for col, row_val in zip(columns, row)
                    ]
                )
            )
            for row in rows
        ]

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
        get_s3_client().upload_file(LOCAL_DB_PATH, DB_BUCKET, DB_KEY)
