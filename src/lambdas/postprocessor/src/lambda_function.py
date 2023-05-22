import traceback
from pprint import pformat
from typing import List, Union

from datapump.clients.aws import get_s3_client, get_s3_path_parts
from datapump.clients.datapump_store import DatapumpConfig, DatapumpStore
from datapump.clients.rw_api import update_area_statuses
from datapump.commands.analysis import Analysis
from datapump.commands.sync import SyncType
from datapump.globals import GLOBALS, LOGGER
from datapump.jobs.geotrellis import FireAlertsGeotrellisJob, GeotrellisJob
from datapump.jobs.jobs import Job, JobStatus
from datapump.jobs.version_update import RasterVersionUpdateJob
from datapump.sync.rw_areas import get_aoi_geostore_ids
from datapump.util.util import log_and_notify_error
from pydantic import parse_obj_as


def handler(event, context):
    LOGGER.info(f"Postprocessing results of map: {pformat(event)}")
    jobs: List[Job] = parse_obj_as(
        List[Union[FireAlertsGeotrellisJob, GeotrellisJob, RasterVersionUpdateJob]],
        event["jobs"],
    )
    failed_jobs = []
    rw_area_jobs = []

    config_client = DatapumpStore()

    for job in jobs:
        LOGGER.info(f"Postprocessing job: {pformat(job.dict())}")

        if isinstance(job, GeotrellisJob):
            sync_types = (
                [job.sync_type]
                if job.sync_type
                else SyncType.get_sync_types(job.table.dataset, job.table.analysis)
            )

            if SyncType.rw_areas in sync_types:
                rw_area_jobs.append(job)

            # add any results with sync enabled to the config table
            if job.status == JobStatus.failed:
                failed_jobs.append(job)
            elif job.status == JobStatus.complete:
                # it's possible to have multiple sync types for a single table
                # (e.g. viirs and geostore), so add all to config table
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
            if job.status == JobStatus.failed:
                failed_jobs.append(job)
            elif job.status == JobStatus.complete:
                config_client.put(
                    DatapumpConfig(
                        analysis_version="",
                        dataset=job.dataset,
                        dataset_version="",
                        analysis=Analysis.create_raster,
                        sync=True,
                        sync_type=job.dataset,
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
        try:
            # update AOIs on RW but only on production
            geostore_ids = get_aoi_geostore_ids(rw_area_jobs[0].features_1x1)
            update_area_statuses(geostore_ids, "saved")
        except Exception:
            log_and_notify_error(
                f"Exception while trying to update user area statuses: {traceback.format_exc()}"
            )
