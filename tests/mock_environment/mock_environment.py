import json
import os

import boto3

from datapump_utils.util import get_date_string, bucket_suffix
from datapump_utils.s3 import s3_client, get_s3_path_parts

CURDIR = os.path.dirname(__file__)
GLAD_ALERTS_PATH = f"s3://gfw-data-lake{bucket_suffix()}/gladalerts/10x10"

os.environ["S3_BUCKET_PIPELINE"] = f"gfw-pipelines{bucket_suffix()}"
os.environ[
    "GEOTRELLIS_JAR"
] = f"s3://gfw-pipelines{bucket_suffix()}/geotrellis/jars/test2.jar"
os.environ["GLAD_ALERTS_PATH"] = GLAD_ALERTS_PATH
os.environ["DATASETS"] = json.dumps(
    {
        "geostore": {
            "gladalerts": {
                "daily_alerts": "testid_daily_alerts_glad",
                "weekly_alerts": "testid_weekly_alerts_glad",
                "summary": "testid_summary_glad",
                "whitelist": "testid_whitelist_glad",
            },
            "annualupdate_minimal": {
                "change": "testid_change_tcl",
                "summary": "testid_summary_tcl",
                "whitelist": "testid_whitelist_tcl",
            },
        },
        "gadm": {
            "gladalerts": {
                "iso": {"weekly_alerts": "testid_weekly_alerts_glad_iso",},
                "adm1": {"weekly_alerts": "testid_weekly_alerts_glad_adm1",},
                "adm2": {
                    "daily_alerts": "testid_daily_alerts_glad_adm2",
                    "weekly_alerts": "testid_weekly_alerts_glad_adm2",
                },
            },
        },
        "wdpa": {
            "gladalerts": {
                "daily_alerts": "testid_daily_alerts_wdpa",
                "weekly_alerts": "testid_weekly_alerts_wdpa",
                "summary": "testid_summary_wdpa",
                "whitelist": "testid_whitelist_wdpa",
            },
        },
    },
)
os.environ["PUBLIC_SUBNET_IDS"] = json.dumps(["test_subnet", "test_subnet"])
os.environ["EC2_KEY_NAME"] = "test_ec2_key_name"
os.environ["EMR_INSTANCE_PROFILE"] = "TEST_EMR_INSTANCE_PROFILE"
os.environ["EMR_SERVICE_ROLE"] = "TEST_SERVICE_ROLE"
os.environ["S3_BUCKET_DATA_LAKE"] = "test_datalake_bucket"


def mock_environment():
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"  # pragma: allowlist secret
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"

    _mock_s3_setup()
    _mock_secrets()


def _mock_s3_setup():
    pipeline_bucket = f"gfw-pipelines{bucket_suffix()}"
    s3_client().create_bucket(Bucket=pipeline_bucket)
    s3_client().create_bucket(Bucket=os.environ["S3_BUCKET_DATA_LAKE"])

    with open(os.path.join(CURDIR, "mock_files/test1.jar"), "r") as test1_jar:
        s3_client().upload_fileobj(
            test1_jar, Bucket=pipeline_bucket, Key="geotrellis/jars/test1.jar"
        )

    with open(os.path.join(CURDIR, "mock_files/test2.jar"), "r") as test2_jar:
        s3_client().upload_fileobj(
            test2_jar, Bucket=pipeline_bucket, Key="geotrellis/jars/test2.jar"
        )

    results_glad = (
        f"geotrellis/results/test/{get_date_string()}/gladalerts_20191119_1245/geostore"
    )
    results_tcl = f"geotrellis/results/test/{get_date_string()}/annualupdate_minimal_20191119_1245/geostore"
    results1 = os.path.join(CURDIR, "mock_files/results1.csv")
    results2 = os.path.join(CURDIR, "mock_files/results2.csv")
    results3 = os.path.join(CURDIR, "mock_files/results3.csv")
    success = os.path.join(CURDIR, "mock_files/_SUCCESS")

    s3_client().upload_fileobj(
        open(results1, "rb"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/daily_alerts/results1.csv",
    )
    s3_client().upload_fileobj(
        open(results1, "rb"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/weekly_alerts/results1.csv",
    )
    s3_client().upload_fileobj(
        open(results1, "rb"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/summary/results1.csv",
    )
    s3_client().upload_fileobj(
        open(results1, "rb"),
        Bucket=pipeline_bucket,
        Key=f"{results_tcl}/change/results1.csv",
    )
    s3_client().upload_fileobj(
        open(results1, "rb"),
        Bucket=pipeline_bucket,
        Key=f"{results_tcl}/summary/results1.csv",
    )

    s3_client().upload_fileobj(
        open(results2, "rb"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/daily_alerts/results2.csv",
    )
    s3_client().upload_fileobj(
        open(results2, "rb"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/weekly_alerts/results2.csv",
    )
    s3_client().upload_fileobj(
        open(results2, "rb"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/summary/results2.csv",
    )
    s3_client().upload_fileobj(
        open(results2, "rb"),
        Bucket=pipeline_bucket,
        Key=f"{results_tcl}/change/results2.csv",
    )
    s3_client().upload_fileobj(
        open(results2, "rb"),
        Bucket=pipeline_bucket,
        Key=f"{results_tcl}/summary/results2.csv",
    )
    s3_client().upload_fileobj(
        open(results3, "rb"),
        Bucket=pipeline_bucket,
        Key=f"{results_glad}/daily_alerts/results3.csv",
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

    glad_alerts_bucket, glad_alerts_prefix = get_s3_path_parts(GLAD_ALERTS_PATH)
    tile1 = os.path.join(CURDIR, "mock_files/tile1.tif")
    tile2 = os.path.join(CURDIR, "mock_files/tile2.tif")

    s3_client().create_bucket(Bucket=glad_alerts_bucket)
    s3_client().upload_fileobj(
        open(tile1, "r"),
        Bucket=glad_alerts_bucket,
        Key=f"{glad_alerts_prefix}/tile1.tif",
    )
    s3_client().upload_fileobj(
        open(tile2, "r"),
        Bucket=glad_alerts_bucket,
        Key=f"{glad_alerts_prefix}/tile2.tif",
    )

    s3_client().upload_fileobj(
        open(
            os.path.join(CURDIR, "mock_files/2020-01-21-0010_2020-01-21-0028.tsv"), "r"
        ),
        Bucket=os.environ["S3_BUCKET_DATA_LAKE"],
        Key=f"nasa_modis_fire_alerts/v6/vector/epsg-4326/nrt/2020-01-20-0030_2020-01-20-0040.tsv",
    )

    s3_client().upload_fileobj(
        open(
            os.path.join(CURDIR, "mock_files/2020-01-21-0010_2020-01-21-0028.tsv"), "r"
        ),
        Bucket=os.environ["S3_BUCKET_DATA_LAKE"],
        Key=f"nasa_modis_fire_alerts/v6/vector/epsg-4326/nrt/2020-01-21-0010_2020-01-21-0028.tsv",
    )


def _mock_secrets():
    client = boto3.client("secretsmanager", region_name="us-east-1")
    client.create_secret(
        Name="gfw-api/token",
        SecretString=json.dumps({"token": "footoken", "email": "foo@bar.org"}),
    )
