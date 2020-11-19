from datapump.globals import LOGGER
from datapump.jobs.jobs import GeotrellisJob, GeotrellisJobStatus


def handler(event, context):
    try:
        job = GeotrellisJob(**event)

        LOGGER.info(f"Running analysis job:\n{job.dict()}")
        if job.status == GeotrellisJobStatus.starting:
            job.start_analysis()
        elif job.status == GeotrellisJobStatus.analyzing:
            job.update_status()

        return job.dict()
    except Exception as e:
        LOGGER.exception(e)
        return {"status": "failed"}
