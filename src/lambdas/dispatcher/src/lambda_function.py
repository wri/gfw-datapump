import json
import pprint
import traceback
from pprint import pformat
from typing import Any, Dict, List, Union
from uuid import uuid1

from pydantic import parse_obj_as
from pydantic.error_wrappers import ValidationError

from datapump.clients.data_api import DataApiClient
from datapump.clients.datapump_store import DatapumpStore
from datapump.commands.analysis import FIRES_ANALYSES, AnalysisCommand
from datapump.commands.continue_jobs import ContinueJobsCommand
from datapump.commands.set_latest import SetLatestCommand
from datapump.commands.sync import SyncCommand
from datapump.commands.version_update import RasterVersionUpdateCommand
from datapump.globals import LOGGER
from datapump.jobs.geotrellis import FireAlertsGeotrellisJob, GeotrellisJob
from datapump.jobs.jobs import Job, JobStatus
from datapump.jobs.version_update import RasterVersionUpdateJob
from datapump.sync.sync import Syncer
from datapump.util.slack import slack_webhook
from datapump.util.util import log_and_notify_error


def handler(event, context):
    try:
        command = parse_obj_as(
            Union[
                AnalysisCommand,
                RasterVersionUpdateCommand,
                SyncCommand,
                ContinueJobsCommand,
                SetLatestCommand,
            ],
            event,
        )
        LOGGER.info(f"Received command:\n{pformat(command.dict())}")
    except ValidationError as e:
        log_and_notify_error(
            f"Validation error parsing the following command:\n"
            f"{json.dumps(event, indent=2)}\n"
            f"Error:\n{e.json(indent=2)}"
        )
        raise e

    jobs: List[Job] = []

    try:
        client = DataApiClient()
        if isinstance(command, AnalysisCommand):
            jobs += _analysis(command, client)
        elif isinstance(command, RasterVersionUpdateCommand):
            jobs += _raster_version_update(command)
        elif isinstance(command, SyncCommand):
            jobs += _sync(command)
        elif isinstance(command, ContinueJobsCommand):
            jobs += command.parameters.dict()["jobs"]
        elif isinstance(command, SetLatestCommand):
            _set_latest(command, client)

        LOGGER.info(f"Dispatching jobs:\n{pformat(jobs)}")
        return {"jobs": jobs}
    except Exception as e:
        log_and_notify_error(
            "Exception while creating jobs for command: "
            f"{pprint.pformat(command)}\n\n"
            f"{traceback.format_exc()}"
        )
        raise e


def _analysis(command: AnalysisCommand, client: DataApiClient) -> List[Dict[str, Any]]:
    jobs = []

    for table in command.parameters.tables:
        asset_uri = client.get_1x1_asset(table.dataset, table.version)
        if table.analysis in FIRES_ANALYSES:
            jobs.append(
                FireAlertsGeotrellisJob(
                    id=str(uuid1()),
                    status=JobStatus.starting,
                    analysis_version=command.parameters.analysis_version,
                    table=table,
                    features_1x1=asset_uri,
                    sync=command.parameters.sync,
                    geotrellis_version=command.parameters.geotrellis_version,
                    alert_type=table.analysis.value,
                ).dict()
            )
        else:
            jobs.append(
                GeotrellisJob(
                    id=str(uuid1()),
                    status=JobStatus.starting,
                    analysis_version=command.parameters.analysis_version,
                    table=table,
                    features_1x1=asset_uri,
                    sync=command.parameters.sync,
                    geotrellis_version=command.parameters.geotrellis_version,
                ).dict()
            )

    return jobs


def _raster_version_update(command: RasterVersionUpdateCommand):
    job = RasterVersionUpdateJob(
        id=str(uuid1()),
        status=JobStatus.starting,
        dataset=command.parameters.dataset,
        version=command.parameters.version,
        content_date_range=command.parameters.content_date_range,
        tile_set_parameters=command.parameters.tile_set_parameters,
        tile_cache_parameters=command.parameters.tile_cache_parameters,
    )
    return [job.dict()]


def _sync(command: SyncCommand):
    jobs = []
    syncer = Syncer(command.parameters.types, command.parameters.sync_version)
    config_client = DatapumpStore()

    for sync_type in command.parameters.types:
        sync_config = config_client.get(sync=True, sync_type=sync_type)
        if not sync_config:
            slack_webhook(
                "WARNING",
                f"No DynamoDB rows found for sync type {sync_type}!"
            )
            LOGGER.warning(f"No DynamoDB rows found for sync type {sync_type}!")
        for row in sync_config:
            syncer_jobs = syncer.build_jobs(row)
            LOGGER.info(f"Processing row {row}, got jobs {syncer_jobs}!")
            if syncer_jobs:
                jobs += [job.dict() for job in syncer_jobs]

    return jobs


def _set_latest(command: SetLatestCommand, data_api_client: DataApiClient):
    config_client = DatapumpStore()
    rows = config_client.get(analysis_version=command.parameters.analysis_version)
    datasets = data_api_client.get_datasets()
    for row in rows:
        ds_prefix = f"{row.dataset}__{row.analysis}__"
        analysis_datasets = [
            ds["dataset"] for ds in datasets if ds["dataset"].startswith(ds_prefix)
        ]

        for ds in analysis_datasets:
            data_api_client.set_latest(ds, row.analysis_version)
