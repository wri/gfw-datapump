from typing import Union, cast
from uuid import uuid1

from pydantic import parse_obj_as, ValidationError
from pprint import pformat

from datapump.globals import LOGGER, GLOBALS
from datapump.clients.data_api import DataApiClient
from datapump.jobs.jobs import JobStatus
from datapump.jobs.geotrellis import GeotrellisJob, FireAlertsGeotrellisJob
from datapump.sync.sync import Syncer
from datapump.clients.datapump_store import DatapumpStore
from datapump.commands import AnalysisCommand, SyncCommand, Analysis


def handler(event, context):
    try:
        command = parse_obj_as(Union[AnalysisCommand, SyncCommand], event)
        client = DataApiClient()

        jobs = []
        LOGGER.info(f"Received command:\n{pformat(command.dict())}")
        if isinstance(command, AnalysisCommand):
            cast(AnalysisCommand, command)
            jobs += _analysis(command, client)
        elif isinstance(command, SyncCommand):
            cast(SyncCommand, command)
            jobs += _sync(command)

        LOGGER.info(f"Dispatching jobs:\n{pformat(jobs)}")
        return {"jobs": jobs}
    except ValidationError as e:
        return {"statusCode": 400, "body": {"message": "Validation error", "detail": e}}
    except Exception as e:
        LOGGER.exception(f"Exception caught while running update: {e}")
        raise e


def _analysis(command: AnalysisCommand, client: DataApiClient):
    jobs = []

    for table in command.parameters.tables:
        asset_uri = client.get_1x1_asset(table.dataset, table.version)
        if table.analysis in [Analysis.viirs, Analysis.modis]:
            job = FireAlertsGeotrellisJob(
                id=str(uuid1()),
                status=JobStatus.starting,
                analysis_version=command.parameters.analysis_version,
                table=table,
                features_1x1=asset_uri,
                sync=command.parameters.sync,
                geotrellis_version=command.parameters.geotrellis_version,
                alert_type=table.analysis.value,
                alert_sources=[
                    f"{GLOBALS.fire_source_paths[table.analysis.value]}/scientific/*.tsv",
                    f"{GLOBALS.fire_source_paths[table.analysis.value]}/near_real_time/*.tsv",
                ],
            )
        else:
            job = GeotrellisJob(
                id=str(uuid1()),
                status=JobStatus.starting,
                analysis_version=command.parameters.analysis_version,
                table=table,
                features_1x1=asset_uri,
                sync=command.parameters.sync,
                geotrellis_version=command.parameters.geotrellis_version,
            )

        jobs.append(job.dict())

    return jobs


def _sync(command: SyncCommand):
    jobs = []
    syncer = Syncer(command.parameters.types, command.parameters.sync_version)

    with DatapumpStore() as config_client:
        for sync_type in command.parameters.types:
            sync_config = config_client.get(sync="true", sync_type=sync_type)
            for row in sync_config:
                job = syncer.build_job(row)
                if job:
                    jobs.append(job.dict())

    return jobs
