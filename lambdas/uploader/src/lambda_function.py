import os
import traceback

from datapump_utils.logger import get_logger
from datapump_utils.util import error
from datapump_utils.jobs import GeotrellisJob, GeotrellisJobStatus
from datapump_utils.data_api_client import DataApiClient

if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"

LOGGER = get_logger(__name__)


def handler(event, context):
    try:
        job = GeotrellisJob(**event)
        client = DataApiClient()

        if job.status == GeotrellisJobStatus.analyzed:
            for table in job.result_tables:
                # convert table.index_columns to usable index
                # create cluster based off index
                client.add_version(
                    table.dataset, table.version, table.source_uri, table.index_columns
                )
                job.status = GeotrellisJobStatus.uploading
        elif job.status == GeotrellisJobStatus.uploading:
            all_saved = True
            for table in job.result_tables:
                status = client.get_version(table.dataset, table.version)["status"]
                if status == "failed":
                    job.status = GeotrellisJobStatus.failed
                    return job

                all_saved &= status == "saved"

            if all_saved:
                job.status = GeotrellisJobStatus.success

            return job
    except Exception as e:
        return error(f"Exception caught while running update: {e}")
