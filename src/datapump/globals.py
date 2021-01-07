import os
import logging
import json
from typing import Optional, List

import pydantic
from pydantic import BaseSettings
from pydantic import Field, PositiveInt

LOGGER = logging.getLogger("datapump")
LOGGER.setLevel(logging.DEBUG)


class EnvSettings(BaseSettings):
    def env_dict(self):
        env = self.dict(exclude_none=True)
        return {key.upper(): str(value) for key, value in env.items()}

    class Config:
        case_sensitive = False
        validate_assignment = True


class Globals(EnvSettings):
    env: str = Field(env="ENV")

    token_secret_id: str = Field("gfw-api/token")
    data_api_uri: str = Field(env="DATA_API_URI")

    aws_region: Optional[str] = Field("us-east-1", env="AWS_REGION")
    s3_bucket_pipeline: str = Field(env="S3_BUCKET_PIPELINE")
    s3_glad_path: str = Field(env="S3_GLAD_PATH")
    ec2_key_name: Optional[str] = Field("", env="EC2_KEY_NAME")
    public_subnet_ids: List[str] = Field(
        json.loads(os.environ.get("PUBLIC_SUBNET_IDS", b"[]"))
    )
    emr_instance_profile: Optional[str] = Field("", env="EMR_INSTANCE_PROFILE")
    emr_service_role: Optional[str] = Field("", env="EMR_SERVICE_ROLE")
    command_runner_jar: Optional[str] = Field(
        "command-runner.jar", env="COMMAND_RUNNER_JAR"
    )

    emr_version: str = Field("emr-6.1.0")

    geotrellis_jar_path = Field("", env="GEOTRELLIS_JAR_PATH")
    worker_count_min: PositiveInt = Field(5)
    worker_count_per_gb_features: PositiveInt = Field(50)

    # if LOCALSTACK_HOSTNAME is set, it means we're running in a mock environment
    # and should use that as the endpoint URI
    localstack_hostname: Optional[str] = Field(None, env="LOCALSTACK_HOSTNAME")
    aws_endpoint_uri: Optional[str] = Field(
        f"http://{localstack_hostname}:4566" if localstack_hostname else None
    )


GLOBALS = Globals()
