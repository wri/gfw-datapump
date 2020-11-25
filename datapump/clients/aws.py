import boto3

from datapump.globals import AWS_REGION, AWS_ENDPOINT_URI


def client_constructor(service: str):
    """Using closure design for a client constructor This way we only need to
    create the client once in central location and it will be easier to
    mock."""
    service_client = None

    def client():
        nonlocal service_client
        if service_client is None:
            service_client = boto3.client(
                service, region_name=AWS_REGION, endpoint_url=AWS_ENDPOINT_URI
            )
        return service_client

    return client


get_s3_client = client_constructor("s3")
get_emr_client = client_constructor("emr")
get_lambda_client = client_constructor("lambda")
get_dynamo_client = client_constructor("dynamodb")
