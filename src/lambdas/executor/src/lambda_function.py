from typing import Union

from datapump.globals import LOGGER
from datapump.jobs.geotrellis import FireAlertsGeotrellisJob, GeotrellisJob
from datapump.jobs.jobs import JobStatus
from datapump.jobs.version_update import RasterVersionUpdateJob
from pydantic import parse_obj_as


def handler(event, context):
    job = parse_obj_as(Union[
        FireAlertsGeotrellisJob, GeotrellisJob, RasterVersionUpdateJob
    ], event)

    try:
        LOGGER.info(f"Running next for job:\n{job.dict()}")
        job.next_step()
    except Exception as e:
        LOGGER.exception(e)
        job.status = JobStatus.failed

    return job.dict()
