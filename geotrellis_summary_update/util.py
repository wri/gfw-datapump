import datetime
import os

from geotrellis_summary_update.logger import get_logger
from geotrellis_summary_update.slack import slack_webhook

LOGGER = get_logger(__name__)
if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"


def get_curr_date_dir_name():
    today = datetime.datetime.today()
    return "{}{}{}".format(today.year, today.month, today.day)


def secret_suffix() -> str:
    """
    Get environment suffix for secret token
    """
    if ENV == "production":
        suffix: str = "prod"
    else:
        suffix = "staging"
    return suffix


def bucket_suffix() -> str:
    """
    Get environment suffix for bucket
    """
    if ENV is None:
        suffix: str = "-dev"
    elif ENV == "production":
        suffix = ""
    else:
        suffix = f"-{ENV}"

    return suffix


def api_prefix() -> str:
    """
    Get environment prefix for API
    """
    if ENV == "production":
        suffix: str = "production"
    else:
        suffix = f"staging"

    return suffix


def error(msg):
    LOGGER.error(msg)
    slack_webhook("ERROR", msg)
    return {"status": "FAILED"}
