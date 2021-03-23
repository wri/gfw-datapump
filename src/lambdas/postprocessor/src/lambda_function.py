import os
from typing import Union, cast, List
from pprint import pformat

from pydantic import parse_obj_as

from datapump.globals import LOGGER
from datapump.jobs.jobs import JobStatus
from datapump.jobs.geotrellis import GeotrellisJob, FireAlertsGeotrellisJob
from datapump.clients.datapump_store import DatapumpStore, DatapumpConfig
from datapump.commands import SyncType, Analysis


def handler(event, context):
    LOGGER.info(f"Postprocessing results of map: {pformat(event)}")
    jobs = parse_obj_as(
        List[Union[FireAlertsGeotrellisJob, GeotrellisJob]], event["jobs"]
    )
    failed_jobs = []

    for job in jobs:
        LOGGER.info(f"Postprocessing job: {pformat(job.dict())}")

        if isinstance(job, GeotrellisJob):
            cast(job, GeotrellisJob)

            # add any results with sync enabled to the config table
            if job.status == JobStatus.failed:
                failed_jobs.append(job)
            elif job.status == JobStatus.complete:
                # it's possible to have multiple sync types for a single table (e.g. viirs and geostore),
                # so add all to config table
                config_client = DatapumpStore()
                sync_types = SyncType.get_sync_types(
                    job.table.dataset, job.table.analysis
                )
                LOGGER.debug(
                    f"Writing entries for {job.table.dataset} - {job.table.analysis} - {sync_types}"
                )

                for sync_type in sync_types:
                    if job.sync_version:
                        config_client.put(
                            DatapumpConfig(
                                analysis_version=job.analysis_version,
                                dataset=job.table.dataset,
                                dataset_version=job.table.version,
                                analysis=job.table.analysis,
                                sync_version=job.sync_version,
                            )
                        )
                    elif job.sync:
                        config_client.put(
                            DatapumpConfig(
                                analysis_version=job.analysis_version,
                                dataset=job.table.dataset,
                                dataset_version=job.table.version,
                                analysis=job.table.analysis,
                                sync=job.sync,
                                sync_type=sync_type,
                                sync_version=None,
                                metadata={
                                    "geotrellis_version": job.geotrellis_version,
                                    "features_1x1": job.features_1x1,
                                },
                            )
                        )

    if failed_jobs:
        LOGGER.error("The following jobs failed: ")
        for job in failed_jobs:
            LOGGER.error(pformat(job.dict()))

        raise Exception("One or more jobs failed. See logs for details.")
