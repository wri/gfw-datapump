import boto3

from datapump_utils.s3 import (
    get_s3_path_parts,
    get_s3_path,
    s3_directory_exists,
)

PATH = "s3://gfw-pipelines-test/geotrellis/features/geostore/test_areas.tsv"
BUCKET = "gfw-pipelines-test"
KEY = "geotrellis/features/geostore/test_areas.tsv"


def test_s3_directory_exists():
    s3_client = boto3.client("s3")
    result = s3_directory_exists(BUCKET, KEY, s3_client)
    assert result


def test_get_s3_path_parts():
    result = get_s3_path_parts(PATH)
    assert result == (
        "gfw-pipelines-test",
        "geotrellis/features/geostore/test_areas.tsv",
    )


def test_get_sr_path():
    result = get_s3_path(BUCKET, KEY)
    assert result == PATH
