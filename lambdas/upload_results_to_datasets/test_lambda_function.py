from moto import mock_emr
import pytest
import os
import boto3

from lambdas.upload_results_to_datasets.lambda_function import handler


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"  # pragma: allowlist secret
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture(scope="function")
def emr():
    with mock_emr():
        yield boto3.client("emr", region_name="us-east-1")


os.environ["ENV"] = "test"


def test_handler():
    NotImplementedError()


def test_check_job_status():
    NotImplementedError()


def test_check_success_files():
    NotImplementedError()


def test_get_analysis_result_paths():
    NotImplementedError()
