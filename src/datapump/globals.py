import os
import logging
import json

ENV = os.environ["ENV"]

LOGGER = logging.getLogger("datapump")
LOGGER.setLevel(logging.DEBUG)

DATA_API_URI = os.environ.get("DATA_API_URI", None)

AWS_REGION = os.environ.get("AWS_REGION", None)
S3_BUCKET_PIPELINE = os.environ.get("S3_BUCKET_PIPELINE", None)
S3_GLAD_PATH = os.environ.get("S3_GLAD_PATH", None)
EC2_KEY_NAME = os.environ.get("EC2_KEY_NAME", "")
PUBLIC_SUBNET_IDS = json.loads(os.environ.get("PUBLIC_SUBNET_IDS", b"[]"))
EMR_INSTANCE_PROFILE = os.environ.get("EMR_INSTANCE_PROFILE", "")
EMR_SERVICE_ROLE = os.environ.get("EMR_SERVICE_ROLE", "")
COMMAND_RUNNER_JAR = os.environ.get("COMMAND_RUNNER_JAR", "command-runner.jar")

EMR_VERSION = "emr-6.1.0"

GEOTRELLIS_JAR_PATH = os.environ.get("GEOTRELLIS_JAR_PATH", "")
WORKER_COUNT_MIN = 5
WORKER_COUNT_PER_GB_FEATURES = 50

# if LOCALSTACK_HOSTNAME is set, it means we're running in a mock environment
# and should use that as the endpoint URI
LOCALSTACK_HOSTNAME = os.environ.get("LOCALSTACK_HOSTNAME", None)
AWS_ENDPOINT_URI = f"http://{LOCALSTACK_HOSTNAME}:4566" if LOCALSTACK_HOSTNAME else None

LOGGER.info(str(AWS_ENDPOINT_URI))
