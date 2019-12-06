from moto import mock_emr, mock_s3, mock_secretsmanager
from geotrellis_summary_update.util import get_curr_date_dir_name
import boto3
import json


def mock_environment():
    _mock_s3_setup()
    _mock_secrets


@mock_s3
def _mock_s3_setup():
    s3_client = boto3.client("s3")

    pipeline_bucket = "gfw-pipelines-dev"
    s3_client.create_bucket(Bucket=pipeline_bucket)
    with open("mock_environment/mock_files/test1.jar", "r") as test1_jar:
        s3_client.upload_fileobj(
            test1_jar, Bucket=pipeline_bucket, Key="geotrellis/jars/test1.jar"
        )

    with open("mock_environment/mock_files/test2.jar", "r") as test2_jar:
        s3_client.upload_fileobj(
            test2_jar, Bucket=pipeline_bucket, Key="geotrellis/jars/test2.jar"
        )

    results_glad = f"geotrellis/results/test/{get_curr_date_dir_name()}/gladalerts_20191119_1245/geostore"
    results_tcl = f"geotrellis/results/test/{get_curr_date_dir_name()}/annualupdate_minimal_20191119_1245/geostore"
    results1 = "mock_environment/mock_files/results1.csv"
    results2 = "mock_environment/mock_files/results1.csv"
    success = "mock_environment/mock_files/_SUCCESS"

    s3_client.upload_fileobj(
        open(results1, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/daily_alerts/results1.csv",
    )
    s3_client.upload_fileobj(
        open(results1, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/weekly_alerts/results1.csv",
    )
    s3_client.upload_fileobj(
        open(results1, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/summary/results1.csv",
    )
    s3_client.upload_fileobj(
        open(results1, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_tcl}/change/results1.csv",
    )
    s3_client.upload_fileobj(
        open(results1, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_tcl}/summary/results1.csv",
    )

    s3_client.upload_fileobj(
        open(results2, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/daily_alerts/results2.csv",
    )
    s3_client.upload_fileobj(
        open(results2, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/weekly_alerts/results2.csv",
    )
    s3_client.upload_fileobj(
        open(results2, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/summary/results2.csv",
    )
    s3_client.upload_fileobj(
        open(results2, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_tcl}/change/results2.csv",
    )
    s3_client.upload_fileobj(
        open(results2, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_tcl}/summary/results2.csv",
    )

    s3_client.upload_fileobj(
        open(success, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/daily_alerts/_SUCCESS",
    )
    s3_client.upload_fileobj(
        open(success, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/weekly_alerts/_SUCCESS",
    )
    s3_client.upload_fileobj(
        open(success, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/summary/_SUCCESS",
    )
    s3_client.upload_fileobj(
        open(success, "r"), Bucket=pipeline_bucket, Key=f"{results_tcl}/change/_SUCCESS"
    )
    s3_client.upload_fileobj(
        open(success, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_tcl}/summary/_SUCCESS",
    )


@mock_secretsmanager
def _mock_secrets():
    client = boto3.client("secretsmanager", region_name="us-east-1")
    client.create_secret(
        Name="gfw-api/staging-token",
        SecretString=json.dumps({"token": "footoken", "email": "foo@bar.org"}),
    )
