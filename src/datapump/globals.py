import json
import logging
import os
from typing import List, Optional

from pydantic import BaseSettings, Field, PositiveInt

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
    env: Optional[str] = Field("dev", env="ENV")

    token_secret_id: str = Field("gfw-api/token")
    data_api_uri: Optional[str] = Field(env="DATA_API_URI")

    aws_region: Optional[str] = Field("us-east-1", env="AWS_REGION")
    s3_bucket_pipeline: str = Field(env="S3_BUCKET_PIPELINE")
    s3_bucket_data_lake: str = Field(env="S3_BUCKET_DATA_LAKE")
    s3_glad_path: Optional[str] = Field(env="S3_GLAD_PATH")
    ec2_key_name: Optional[str] = Field("", env="EC2_KEY_NAME")
    public_subnet_ids: List[str] = Field(
        json.loads(os.environ.get("PUBLIC_SUBNET_IDS", b"[]"))
    )
    emr_instance_profile: Optional[str] = Field("", env="EMR_INSTANCE_PROFILE")
    emr_service_role: Optional[str] = Field("", env="EMR_SERVICE_ROLE")
    command_runner_jar: Optional[str] = Field(
        "command-runner.jar", env="COMMAND_RUNNER_JAR"
    )

    emr_version: str = Field("emr-6.3.1")

    geotrellis_jar_path = Field(
        "s3://gfw-pipelines/geotrellis/jars", env="GEOTRELLIS_JAR_PATH"
    )
    worker_count_min: PositiveInt = Field(10)
    worker_count_per_gb_features: PositiveInt = Field(50)

    # if LOCALSTACK_HOSTNAME is set, it means we're running in a mock environment
    # and should use that as the endpoint URI
    aws_endpoint_uri: Optional[str] = Field(
        f"http://{os.environ['LOCALSTACK_HOSTNAME']}:4566"
        if "LOCALSTACK_HOSTNAME" in os.environ
        else None
    )

    max_versions: int = Field(4, env="MAX_VERSIONS")
    datapump_table_name: Optional[str] = Field(env="DATAPUMP_TABLE_NAME")

    geotrellis_iso_start: str = Field(env="GEOTRELLIS_ISO_START")
    geotrellis_iso_end: str = Field(env="GEOTRELLIS_ISO_END")

    gcs_key_secret_arn: Optional[str] = Field(None, env="GCS_KEY_SECRET_ARN")

    google_application_credentials = Field(
        "/tmp/.gcs/private_key.json", env="GOOGLE_APPLICATION_CREDENTIALS"
    )


GLOBALS = Globals()
