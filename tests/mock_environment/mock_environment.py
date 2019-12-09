import json
import os

import boto3

from geotrellis_summary_update.util import get_curr_date_dir_name, bucket_suffix
from geotrellis_summary_update.s3 import s3_client

CURDIR = os.path.dirname(__file__)


def mock_environment():
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"  # pragma: allowlist secret
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ[
        "GEOTRELLIS_JAR"
    ] = f"s3://gfw-pipelines{bucket_suffix()}/geotrellis/jars/test2.jar"

    _mock_s3_setup()
    _mock_secrets()


def _mock_s3_setup():
    pipeline_bucket = f"gfw-pipelines{bucket_suffix()}"
    s3_client().create_bucket(Bucket=pipeline_bucket)
    with open(os.path.join(CURDIR, "mock_files/test1.jar"), "r") as test1_jar:
        s3_client().upload_fileobj(
            test1_jar, Bucket=pipeline_bucket, Key="geotrellis/jars/test1.jar"
        )

    with open(os.path.join(CURDIR, "mock_files/test2.jar"), "r") as test2_jar:
        s3_client().upload_fileobj(
            test2_jar, Bucket=pipeline_bucket, Key="geotrellis/jars/test2.jar"
        )

    results_glad = f"geotrellis/results/test/{get_curr_date_dir_name()}/gladalerts_20191119_1245/geostore"
    results_tcl = f"geotrellis/results/test/{get_curr_date_dir_name()}/annualupdate_minimal_20191119_1245/geostore"
    results1 = os.path.join(CURDIR, "mock_files/results1.csv")
    results2 = os.path.join(CURDIR, "mock_files/results1.csv")
    success = os.path.join(CURDIR, "mock_files/_SUCCESS")

    s3_client().upload_fileobj(
        open(results1, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/daily_alerts/results1.csv",
    )
    s3_client().upload_fileobj(
        open(results1, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/weekly_alerts/results1.csv",
    )
    s3_client().upload_fileobj(
        open(results1, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/summary/results1.csv",
    )
    s3_client().upload_fileobj(
        open(results1, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_tcl}/change/results1.csv",
    )
    s3_client().upload_fileobj(
        open(results1, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_tcl}/summary/results1.csv",
    )

    s3_client().upload_fileobj(
        open(results2, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/daily_alerts/results2.csv",
    )
    s3_client().upload_fileobj(
        open(results2, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/weekly_alerts/results2.csv",
    )
    s3_client().upload_fileobj(
        open(results2, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/summary/results2.csv",
    )
    s3_client().upload_fileobj(
        open(results2, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_tcl}/change/results2.csv",
    )
    s3_client().upload_fileobj(
        open(results2, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_tcl}/summary/results2.csv",
    )

    s3_client().upload_fileobj(
        open(success, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/daily_alerts/_SUCCESS",
    )
    s3_client().upload_fileobj(
        open(success, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/weekly_alerts/_SUCCESS",
    )
    s3_client().upload_fileobj(
        open(success, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/summary/_SUCCESS",
    )
    s3_client().upload_fileobj(
        open(success, "r"), Bucket=pipeline_bucket, Key=f"{results_tcl}/change/_SUCCESS"
    )
    s3_client().upload_fileobj(
        open(success, "r"),
        Bucket=pipeline_bucket,
        Key=f"{results_tcl}/summary/_SUCCESS",
    )


def _mock_secrets():
    client = boto3.client("secretsmanager", region_name="us-east-1")
    client.create_secret(
        Name="gfw-api/staging-token",
        SecretString=json.dumps({"token": "footoken", "email": "foo@bar.org"}),
    )
