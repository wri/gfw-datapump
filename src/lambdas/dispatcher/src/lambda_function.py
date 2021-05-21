from pprint import pformat
from typing import Any, Dict, List, Union, cast
from uuid import uuid1

from datapump.clients.data_api import DataApiClient
from datapump.clients.datapump_store import DatapumpStore
from datapump.commands import Analysis, AnalysisCommand, VersionUpdateCommand, SetLatestCommand, SyncCommand, \
    UpdatableDatasets
from datapump.globals import LOGGER
from datapump.jobs.geotrellis import (
    ContinueGeotrellisJobsCommand,
    FireAlertsGeotrellisJob,
    GeotrellisJob,
)
from datapump.jobs.version_update import UpdateRADDJob, UpdateGLADS2Job
from datapump.jobs.jobs import JobStatus
from datapump.sync.sync import Syncer
from pydantic import ValidationError, parse_obj_as


def handler(event, context):
    try:
        command = parse_obj_as(
            Union[
                AnalysisCommand,
                VersionUpdateCommand,
                SyncCommand,
                ContinueGeotrellisJobsCommand,
                SetLatestCommand,
            ],
            event,
        )
        client = DataApiClient()

        jobs = []
        LOGGER.info(f"Received command:\n{pformat(command.dict())}")
        if isinstance(command, AnalysisCommand):
            cast(AnalysisCommand, command)
            jobs += _analysis(command, client)
        elif isinstance(command, VersionUpdateCommand):
            cast(VersionUpdateCommand, command)
            jobs += _version_update(command)
        elif isinstance(command, SyncCommand):
            cast(SyncCommand, command)
            jobs += _sync(command)
        elif isinstance(command, ContinueGeotrellisJobsCommand):
            cast(ContinueGeotrellisJobsCommand, command)
            jobs += command.parameters.dict()["jobs"]
        elif isinstance(command, SetLatestCommand):
            cast(SetLatestCommand, command)
            _set_latest(command, client)

        LOGGER.info(f"Dispatching jobs:\n{pformat(jobs)}")
        return {"jobs": jobs}
    except ValidationError as e:
        return {"statusCode": 400, "body": {"message": "Validation error", "detail": e}}
    except Exception as e:
        LOGGER.exception(f"Exception caught while running update: {e}")
        raise e


def _analysis(command: AnalysisCommand, client: DataApiClient) -> List[Dict[str, Any]]:
    jobs = []

    for table in command.parameters.tables:
        asset_uri = client.get_1x1_asset(table.dataset, table.version)
        if table.analysis in [Analysis.viirs, Analysis.modis]:
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


def _version_update(command: VersionUpdateCommand):
    ds = command.parameters.dataset
    # TODO: Put datasets/functions in a dictionary?
    if ds == UpdatableDatasets.wur_radd_alerts:
        job = UpdateRADDJob(
            id=str(uuid1()),
            status=JobStatus.starting,
            dataset=ds,
            version=command.parameters.version,
            source_uri=command.parameters.source_uri,
        )
    elif ds == UpdatableDatasets.umd_glad_sentinel2_alerts:
        job = UpdateGLADS2Job(
            id=str(uuid1()),
            status=JobStatus.starting,
            dataset=ds,
            version=command.parameters.version,
            source_uri=command.parameters.source_uri,
        )
    else:
        raise Exception(f"Unknown dataset {ds}")
    return [job.dict()]


def _sync(command: SyncCommand):
    jobs = []
    syncer = Syncer(command.parameters.types, command.parameters.sync_version)
    config_client = DatapumpStore()

    for sync_type in command.parameters.types:
        sync_config = config_client.get(sync=True, sync_type=sync_type)
        for row in sync_config:
            job = syncer.build_job(row)
            if job:
                jobs.append(job.dict())

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
