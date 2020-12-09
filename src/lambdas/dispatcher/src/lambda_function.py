import os
from typing import List, Union, cast
from uuid import uuid1

from pydantic import BaseModel, parse_obj_as, ValidationError
from pprint import pformat

from datapump.globals import LOGGER
from datapump.clients.data_api import DataApiClient
from datapump.jobs.jobs import AnalysisInputTable, AnalysisTable, JobStatus
from datapump.jobs.geotrellis import GeotrellisJob
from datapump.sync.sync import SyncType, Syncer
from datapump.clients.datapump_store import DatapumpStore


# changing something
# environment should be set via environment variable. This can be done when deploying the lambda function.
if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"


class UpdateCommand(BaseModel):
    command: str

    class UpdateParameters(BaseModel):
        analysis_version: str
        geotrellis_version: str
        tables: List[AnalysisInputTable]

    parameters: UpdateParameters


class SyncCommand(BaseModel):
    command: str

    class SyncParameters(BaseModel):
        types: List[SyncType]
        sync_version: str = None
        tables: List[AnalysisTable] = []

    parameters: SyncParameters


def handler(event, context):
    try:
        command = parse_obj_as(Union[UpdateCommand, SyncCommand], event)
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
                    analysis_version=command.parameters.analysis_version,
                    table=table,
                    features_1x1=asset_uri,
                    sync=True,  # TODO take as parameter too?
                    geotrellis_version=command.parameters.geotrellis_version,
                )
                jobs.append(job.dict())

        elif isinstance(command, SyncCommand):
            cast(SyncCommand, command)
            syncer = Syncer(command.parameters.types, command.parameters.sync_version)

            config_client = DatapumpStore()
            if command.parameters.tables:
                # TODO filter to specific tables
                pass
            else:
                for sync_type in command.parameters.types:
                    LOGGER.debug("HERE")
                    LOGGER.debug(sync_type)
                    sync_config = config_client.get(sync="true", sync_type=sync_type)
                    LOGGER.debug(sync_config)
                    for row in sync_config:
                        job = syncer.build_job(row)
                        if job:
                            jobs.append(job.dict())

            config_client.close()

        LOGGER.info(f"Dispatching jobs:\n{pformat(jobs)}")
        return {"jobs": jobs}
    except ValidationError as e:
        return {"statusCode": 400, "body": {"message": "Validation error", "detail": e}}
    except Exception as e:
        return LOGGER.exception(f"Exception caught while running update: {e}")
