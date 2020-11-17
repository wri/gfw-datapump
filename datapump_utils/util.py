from datetime import date
import os

from datapump_utils.logger import get_logger
from datapump_utils.slack import slack_webhook

LOGGER = get_logger(__name__)
if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"


def get_date_string():
    return date.today().strftime("%Y-%m-%d")


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
    LOGGER.exception(msg)
    slack_webhook("ERROR", msg)
    return {"status": "FAILED"}
