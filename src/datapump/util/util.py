from datetime import date

from ..globals import GLOBALS, LOGGER
from ..util.slack import slack_webhook


def get_date_string():
    return date.today().strftime("%Y-%m-%d")


def secret_suffix() -> str:
    """
    Get environment suffix for secret token
    """
    if GLOBALS.env == "production":
        suffix: str = "prod"
    else:
        suffix = "staging"
    return suffix


def bucket_suffix() -> str:
    """
    Get environment suffix for bucket
    """
    if GLOBALS.env is None:
        suffix: str = "-dev"
    elif GLOBALS.env == "production":
        suffix = ""
    else:
        suffix = f"-{GLOBALS.env}"

    return suffix


def api_prefix() -> str:
    """
    Get environment prefix for API
    """
    if GLOBALS.env == "production":
        suffix: str = "production"
    else:
        suffix = "staging"

    return suffix


def error(msg):
    LOGGER.exception(msg)
    slack_webhook("ERROR", msg)
    return {"status": "FAILED"}
