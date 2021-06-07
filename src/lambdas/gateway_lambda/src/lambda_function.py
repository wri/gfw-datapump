from datapump.globals import LOGGER


def handler(event, context):

    LOGGER.info("Lambda running!")

    return {"Hello": "world"}
