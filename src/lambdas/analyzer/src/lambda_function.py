from typing import Union

from pydantic import parse_obj_as

from datapump.globals import LOGGER
from datapump.jobs.geotrellis import FireAlertsGeotrellisJob, GeotrellisJob
from datapump.jobs.jobs import JobStatus


def handler(event, context):
    try:
        job = parse_obj_as(Union[FireAlertsGeotrellisJob, GeotrellisJob], event)

        LOGGER.info(f"Running analysis job:\n{job.dict()}")
        if job.status == JobStatus.starting:
            LOGGER.info(f"Starting job {job.id}")
            job.start_analysis()
        elif job.status == JobStatus.analyzing:
            LOGGER.info(f"Job {job.id} still analyzing...")
            job.update_status()

        return job.dict()
    except Exception as e:
        LOGGER.exception(e)
        return {"status": "failed"}
