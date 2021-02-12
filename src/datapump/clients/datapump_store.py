import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

from botocore.exceptions import ClientError
from pydantic import BaseModel

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
    sync_version: Optional[str] = None
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
                sync_version varchar(255),
                metadata json
            )
            """
            self.conn.execute(create_sql)
            self.conn.commit()

        return self

    def add(self, config_row: DatapumpConfig) -> None:
        """
        Create entries for each table in new version
        :param version: New version
        :param tables: List of all tables to include in version
        :return: None
        """

        # check if entry already exists
        existing_row = self.get(**config_row.dict())
        if existing_row:
            LOGGER.info(f"Row already exists, skipping write: {existing_row}")
            return

        row_values: List[Optional[str]] = []
        for key, val in config_row.dict().items():
            if not val:
                row_values.append(None)
            elif key == "metadata":
                row_values.append(json.dumps(val))
            else:
                row_values.append(str(val).lower())

        LOGGER.info(f"Executing add query with row values: {row_values}")
        self.conn.execute("INSERT INTO datapump VALUES(?,?,?,?,?,?,?,?)", row_values)
        self.conn.commit()

    def remove(
        self, analysis_version: str, dataset: str, dataset_version: str, analysis: str
    ):
        self.conn.execute(
            """
            DELETE FROM datapump
            WHERE analysis_version = ?
                AND dataset = ?
                AND dataset_version = ?
                AND analysis = ?
        """,
            [analysis_version, dataset, dataset_version, analysis],
        )
        self.conn.commit()

    def update_sync_version(self, sync_version: str, **kwargs) -> None:
        sql = f"UPDATE datapump SET sync_version = '{sync_version}'"

        if kwargs:
            sql += " WHERE " + " AND ".join(
                f"{k} = '{v}'" for k, v in kwargs.items() if k != "metadata"
            )

        LOGGER.info(f"Executing update query: {sql}")
        self.conn.execute(sql)
        self.conn.commit()

    def get(self, **kwargs) -> List[DatapumpConfig]:
        sql = "SELECT * FROM datapump"

        if kwargs:
            sql += " WHERE " + " AND ".join(
                f"{k} = '{v}'" for k, v in kwargs.items() if k != "metadata"
            )

        LOGGER.info(f"Executing select query: {sql}")
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
