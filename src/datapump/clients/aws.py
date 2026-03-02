from urllib.parse import urlparse

import boto3
from botocore.config import Config

from ..globals import GLOBALS

config = Config(retries=dict(max_attempts=0), read_timeout=300)


def client_constructor(service: str):
    """Using closure design for a client constructor This way we only need to
    create the client once in central location and it will be easier to
    mock."""
    service_client = None

    def client():
        nonlocal service_client
        if service_client is None:
            service_client = boto3.client(
                service,
                region_name=GLOBALS.aws_region,
                endpoint_url=GLOBALS.aws_endpoint_uri,
                config=config,
            )
        return service_client

    return client


get_s3_client = client_constructor("s3")
get_emr_client = client_constructor("emr")
get_lambda_client = client_constructor("lambda")
get_dynamo_client = client_constructor("dynamodb")
get_secrets_manager_client = client_constructor("secretsmanager")


def get_s3_path_parts(path):
    parsed = urlparse(path)
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    return bucket, key


def get_s3_path(bucket, key):
    return "s3://{}/{}".format(bucket, key)
