import traceback
from typing import Union

from datapump.globals import LOGGER
from datapump.jobs.geotrellis import FireAlertsGeotrellisJob, GeotrellisJob
from datapump.jobs.jobs import Job, JobStatus
from datapump.jobs.version_update import RasterVersionUpdateJob
from datapump.util.util import log_and_notify_error, slack_webhook
from pydantic import parse_obj_as


def handler(event, context):
    job: Job = parse_obj_as(
        Union[FireAlertsGeotrellisJob, GeotrellisJob, RasterVersionUpdateJob], event
    )

    try:
        LOGGER.info(f"Running next for job:\n{job.dict()}")
        job.next_step()

        if job.status == JobStatus.complete:
            slack_webhook("info", job.success_message())

    except Exception:
        job.errors.append(traceback.format_exc())
        log_and_notify_error(job.error_message())
        job.status = JobStatus.failed

    return job.dict()
