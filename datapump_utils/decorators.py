from functools import wraps
from typing import Callable

from datapump_utils.exceptions import (
    EmptyResponseException,
    UnexpectedResponseError,
)
from datapump_utils.logger import get_logger

LOGGER = get_logger(__name__)


def api_response_checker(endpoint: str):
    def inner_function(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)

            if "errors" in response.keys():
                message = f"Failed to fetch {endpoint}", response["errors"]
                LOGGER.exception(message)
                raise UnexpectedResponseError(message)
            elif "data" not in response.keys():
                message = (
                    f"Failed to fetch {endpoint}. No data object found in response."
                )
                LOGGER.exception(message)
                raise UnexpectedResponseError(message)
            elif not response["data"]:
                message = f"No {endpoint} found"
                LOGGER.info(message)
                raise EmptyResponseException(message)
            else:
                LOGGER.debug(f"Response: {response}")
                return response

        return wrapper

    return inner_function
