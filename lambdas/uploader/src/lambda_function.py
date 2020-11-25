import os

from datapump.util.logger import get_logger
from datapump.util.util import error
from datapump.jobs.jobs import JobStatus
from datapump.jobs.geotrellis import GeotrellisJob
from datapump.clients.data_api import DataApiClient

if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"

LOGGER = get_logger(__name__)


def handler(event, context):
    try:
        job = GeotrellisJob(**event)
        client = DataApiClient()

        if job.status == JobStatus.analyzed:
            for table in job.result_tables:
                # convert table.index_columns to usable index
                # create cluster based off index
                client.add_version(
                    table.dataset, table.version, table.source_uri, table.index_columns, table.index_columns
                )
                job.status = JobStatus.uploading
        elif job.status == JobStatus.uploading:
            all_saved = True
            for table in job.result_tables:
                status = client.get_version(table.dataset, table.version)["status"]
                if status == "failed":
                    job.status = JobStatus.failed
                    return job

                all_saved &= status == "saved"

            if all_saved:
                job.status = JobStatus.complete

        return job.dict()
    except Exception as e:
        LOGGER.exception(e)
        job.status = JobStatus.failed
        return job.dict()
