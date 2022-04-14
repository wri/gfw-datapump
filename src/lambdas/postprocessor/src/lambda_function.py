from pprint import pformat
from typing import List, Union, cast

from datapump.clients.aws import get_s3_client, get_s3_path_parts
from datapump.clients.datapump_store import DatapumpConfig, DatapumpStore
from datapump.clients.rw_api import update_area_statuses
from datapump.commands.sync import SyncType
from datapump.globals import GLOBALS, LOGGER
from datapump.jobs.geotrellis import FireAlertsGeotrellisJob, GeotrellisJob
from datapump.jobs.jobs import JobStatus
from datapump.jobs.version_update import RasterVersionUpdateJob
from datapump.sync.rw_areas import get_aoi_geostore_ids
from datapump.util.slack import slack_webhook
from pydantic import parse_obj_as

from datapump.commands.analysis import Analysis


def handler(event, context):
    LOGGER.info(f"Postprocessing results of map: {pformat(event)}")
    jobs = parse_obj_as(
        List[Union[FireAlertsGeotrellisJob, GeotrellisJob, RasterVersionUpdateJob]],
        event["jobs"],
    )
    failed_jobs = []
    rw_area_jobs = []

    config_client = DatapumpStore()

    for job in jobs:
        LOGGER.info(f"Postprocessing job: {pformat(job.dict())}")

        if isinstance(job, GeotrellisJob):
            cast(job, GeotrellisJob)

            sync_types = (
                [job.sync_type]
                if job.sync_type
                else SyncType.get_sync_types(job.table.dataset, job.table.analysis)
            )

            if SyncType.rw_areas in sync_types:
                rw_area_jobs.append(job)

            job_type_slack = "Sync" if job.sync_version else "Job"
            # add any results with sync enabled to the config table
            if job.status == JobStatus.failed:
                slack_webhook(
                    "error",
                    f"{job_type_slack} failed for analysis {job.table.analysis} on dataset {job.table.dataset}",
                )
                failed_jobs.append(job)
            elif job.status == JobStatus.complete:
                slack_webhook(
                    "info",
                    f"{job_type_slack} succeeded for analysis {job.table.analysis} on dataset {job.table.dataset}!",
                )

                # it's possible to have multiple sync types for a single table (e.g. viirs and geostore),
                # so add all to config table
                LOGGER.debug(
                    f"Writing entries for {job.table.dataset} - {job.table.analysis} - {sync_types}"
                )

                for sync_type in sync_types:
                    if job.sync_version:
                        config_client.update_sync_version(
                            DatapumpConfig(
                                analysis_version=job.analysis_version,
                                dataset=job.table.dataset,
                                dataset_version=job.table.version,
                                analysis=job.table.analysis,
                                sync=True,
                                sync_type=job.sync_type,
                            ),
                            job.sync_version,
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
                                metadata={
                                    "geotrellis_version": job.geotrellis_version,
                                    "features_1x1": job.features_1x1,
                                },
                            )
                        )
        elif isinstance(job, RasterVersionUpdateJob):
            cast(job, RasterVersionUpdateJob)

            if job.status == JobStatus.failed:
                slack_webhook(
                    "error",
                    f"Raster tile generation failed for dataset {job.dataset} with version {job.version}",
                )
                failed_jobs.append(job)
            elif job.status == JobStatus.complete:
                slack_webhook(
                    "info",
                    f"Raster tile generation succeeded for dataset {job.dataset} with version {job.version}!",
                )

                config_client.put(
                    DatapumpConfig(
                        analysis_version=job.version,
                        dataset=job.dataset,
                        dataset_version=job.version,
                        analysis=Analysis.create_raster,
                        sync=True,
                        sync_type=job.dataset
                    )
                )

    if failed_jobs:
        LOGGER.error("The following jobs failed: ")
        for job in failed_jobs:
            LOGGER.error(pformat(job.dict()))

        if rw_area_jobs:
            # delete AOI tsv file to rollback from failed update
            LOGGER.info(f"Rolling back AOI input file: {rw_area_jobs[0].features_1x1}")
            bucket, key = get_s3_path_parts(rw_area_jobs[0].features_1x1)
            get_s3_client().delete_object(Bucket=bucket, Key=key)

        raise Exception("One or more jobs failed. See logs for details.")

    if rw_area_jobs and GLOBALS.env == "production":
        # update AOIs on RW but only on production
        geostore_ids = get_aoi_geostore_ids(rw_area_jobs[0].features_1x1)
        update_area_statuses(geostore_ids, "saved")
