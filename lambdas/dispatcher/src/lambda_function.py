import os
from typing import List, Union, cast
from uuid import uuid1

from pydantic import BaseModel, parse_obj_as
from pprint import pformat

from datapump.util.logger import get_logger
from datapump.clients.data_api import DataApiClient
from datapump.jobs.jobs import Job, JobStatus, Analysis,AnalysisInputTable
from datapump.jobs.geotrellis import GeotrellisJob
# from datapump.sync.sync import SyncType, sync, Sync


# changing something
# environment should be set via environment variable. This can be done when deploying the lambda function.
if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"

LOGGER = get_logger(__name__)


"""
{
    "command": "update":
    "parameters": {
        "analyses": {
            "gadm": ["tcl", "glad", "viirs", "modis"],
            "kba": ["viirs]
        }
    }
}

{
    "command": "sync"
    "parameters": [
        {
            "dataset": "wdpa_protected_areas",
            "version": "vQ42020",
            "analyses": ["glad", "viirs", "modis"],
        },
        {
            "dataset": "kba",
            "version": "vQ42020",
            "analyses": ["glad", "viirs", "modis"],
        }
    ]
}

{
    "command": "continue",
    "parameters: {
        "job_ids": []
    }
}
"""


class UpdateCommand(BaseModel):
    command: str

    class Parameters(BaseModel):
        version: str
        geotrellis_version: str
        tables: List[AnalysisInputTable]

    parameters: Parameters


# class SyncCommand(BaseModel):
#     command: str
#
#     # class SyncVersions(BaseModel):
#     #     class FeatureAnalysis(BaseModel):
#     #         feature_type: str
#     #         analysis: Analysis
#     #
#     #     type: SyncType
#     #     version: str
#     #     analyses: List[AnalysisInputTable] = None  # optional, to filter to specific analyses to run
#     #
#     class Parameters(BaseModel):
#         version: str
#         types: List[SyncType]
#
#     parameters: Parameters


class JobMap(BaseModel):
    jobs: List[Job]


def handler(event, context):
    try:
        command = parse_obj_as(Union[UpdateCommand], event)
        client = DataApiClient()

        jobs = []
        LOGGER.info(f"Received command:\n{pformat(command.dict())}")
        if isinstance(command, UpdateCommand):
            cast(UpdateCommand, command)

            for table in command.parameters.tables:
                asset_uri = client.get_1x1_asset(table.dataset, table.version)
                job = GeotrellisJob(
                    id=str(uuid1()),
                    status=JobStatus.starting,
                    version=command.parameters.version,
                    table=table,
                    features_1x1=asset_uri,
                    geotrellis_jar_version=command.parameters.geotrellis_version
                )
                jobs.append(job)

        # elif isinstance(command, SyncCommand):
        #     cast(SyncCommand, command)
        #
        #     # sync_types = set([sync_version.type for sync_version in command.parameters])
        #     version = command.parameters.types if command.parameters.types is not None else Sync.get_latest_version()
        #     for type in command.parameters.types:
        #         sync(type, version)
        #
        #
        #     # ALTERNATIVELY
        #     # scan data API for datasets with this version?
        #     # or just put a file with version name and such?
        #     # get all geostore jobs
        #
        #     # somehow_get_datasets_to_update()
        #     # create_job_for_each()
        #
        #     # schema: main_version, analysis, dataset, last_job,
        #     # sync table: all syncs and versions
        #     # if sync version doesn't exist, sync and rerun
        #     # if it doesn't, get output for each sync type and re-use for an update
        #     # OR simpler, just COMPLETELY roll back everything if a sync fails and redo
        #
        #     # for sync_version in command.parameters:

        job_map = JobMap(jobs=jobs).dict()
        LOGGER.info(f"Dispatching jobs:\n{pformat(job_map)}")
        return job_map


    except Exception as e:
        return LOGGER.exception(f"Exception caught while running update: {e}")