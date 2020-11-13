import os
import traceback

from datapump_utils.logger import get_logger
from datapump_utils.util import error
from datapump_utils.jobs import GeotrellisJob
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

        for table in job.result_tables:
            # convert table.index_columns to usable index
            # create cluster based off index
            client.add_version(table.dataset, table.version, table.source_uri)

    except Exception as e:
        return error(f"Exception caught while running update: {e}")
