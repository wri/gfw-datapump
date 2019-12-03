import os

from geotrellis_summary_update.exceptions import UnexpectedResponseError
from geotrellis_summary_update.util import api_prefix

from lambdas.update_new_area_statuses.lambda_function import (
    handler,
    get_aoi_geostore_ids,
    update_aoi_status,
)

os.environ["ENV"] = "test"
job_flow_id = "TESTID"


def test_handler():
    # Still need to work on the return values
    raise NotImplementedError


def test_get_aoi_geostore_ids():

    aoi_src = "s3://gfw-pipelines-test/geotrellis/features/geostore/test_areas.tsv"
    result = get_aoi_geostore_ids(aoi_src)

    assert len(result) == 34


def test_update_aoi_status(requests_mock):

    url = f"https://{api_prefix()}-api.globalforestwatch.org/v1/area"
    geostore_ids = {
        "069b603da1c881cf0fc193c39c3687bb",  # pragma: allowlist secret
        "0883910a878fdda456dbd72ec151126e",  # pragma: allowlist secret
    }

    status_code = 204
    requests_mock.patch(url, status_code=status_code)
    result = update_aoi_status(geostore_ids)
    assert result == status_code

    status_code = 500
    try:
        requests_mock.patch(url, status_code=status_code)
        result = update_aoi_status(geostore_ids)
    except Exception as e:
        assert isinstance(e, UnexpectedResponseError)
