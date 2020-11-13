from datapump_utils.util import error
from datapump_utils.jobs import GeotrellisJob, JobStatus


def handler(event, context):
    try:
        job = GeotrellisJob(**event)

        if job.status == JobStatus.pending:
            job.start_analysis()
        elif job.status == JobStatus.running:
            job.update_status()

        return job.dict()
    except Exception as e:
        return error(f"Exception caught while running update: {e}")
