import json

from datapump.globals import LOGGER


def handler(event, context):

    LOGGER.info("Lambda running!")

    return {
        "statusCode": 200,
        "body": json.dumps({"Hello": "world"})
    }
