from enum import Enum
from datetime import datetime
from uuid import uuid1

from datapump.jobs.jobs import JobStatus
from datapump.sync.fire_alerts import process_active_fire_alerts
from datapump.sync.rw_areas import create_1x1_tsv
from datapump.clients.aws import get_dynamo_client
from datapump.jobs.geotrellis import GeotrellisJob, AnalysisInputTable


class SyncType(str, Enum):
    viirs = "viirs"
    modis = "modis"
    glad = "glad"
    rw_areas = "rw_areas"


def sync(type: SyncType, version: str):
    if type == SyncType.rw_areas:
        RWAreasSync.sync(version)


class Sync:
    @staticmethod
    def sync(version: str):
        pass

    @staticmethod
    def get_latest_version():
        return f"v{datetime.strptime('%Y%m%d')}"

    @staticmethod
    def get_sync_jobs(version: str):
        # get dynamo client
        client = get_dynamo_client()
        # get rows where sync is true and version in sync
        TABLE_NAME = ""

        results = client.query(
            ExpressionAttributeValues={
                ":version": version
            },
            KeyConditionExpression="version = :version AND dataset = :dataset",
            TableName=TABLE_NAME,
        )

        jobs = []
        for item in results["Item"]:
            analyses = item['analyses']
            dataset = item['dataset']

            # GeotrellisJob(
            #     id=str(uuid1()),
            #     status=JobStatus.starting,
            #     version=version,
            #     table=table,
            #     features_1x1=sync_uri,
            #     feature_type=feature_type,
            #     geotrellis_jar_version=geotrellis_jar
            # )

        pass


class ViirsSync(Sync):
    @staticmethod
    def sync(version: str):
        viirs_path = [process_active_fire_alerts("VIIRS")]


class ModisSync(Sync):
    @staticmethod
    def sync(version: str):
        viirs_path = [process_active_fire_alerts("VIIRS")]


class GladSync(Sync):
    @staticmethod
    def sync(version: str):
        pass


class RWAreasSync(Sync):
    @staticmethod
    def sync(version: str):
        create_1x1_tsv(version)