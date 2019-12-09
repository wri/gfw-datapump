import os

from geotrellis_summary_update.exceptions import UnexpectedResponseError
from geotrellis_summary_update.util import api_prefix

from lambdas.update_new_area_statuses.src.lambda_function import (
    handler,
    get_aoi_geostore_ids,
    update_aoi_status,
)

os.environ["ENV"] = "test"
job_flow_id = "TESTID"


def test_handler(requests_mock):
    aoi_src = "s3://gfw-pipelines-test/geotrellis/features/geostore/test_areas.tsv"
    geostore_ids = get_aoi_geostore_ids(aoi_src)

    for geostore_id in geostore_ids:
        url = f"https://{api_prefix()}-api.globalforestwatch.org/v1/area/{geostore_id}"
        requests_mock.patch(url, status_code=200)

    result = handler({"feature_src": aoi_src}, None)
    assert result == {"status": "SUCCESS"}


def test_get_aoi_geostore_ids():
    aoi_src = "s3://gfw-pipelines-test/geotrellis/features/geostore/test_areas.tsv"
    result = get_aoi_geostore_ids(aoi_src)

    assert len(result) == 34


def test_update_aoi_status(requests_mock):
    geostore_id = "069b603da1c881cf0fc193c39c3687bb"  # pragma: allowlist secret
    url = f"https://{api_prefix()}-api.globalforestwatch.org/v1/area/{geostore_id}"

    status_code = 200
    requests_mock.patch(url, status_code=status_code)
    result = update_aoi_status(geostore_id)
    assert result == status_code

    status_code = 500
    try:
        requests_mock.patch(url, status_code=status_code)
        result = update_aoi_status(geostore_id)
    except Exception as e:
        assert isinstance(e, UnexpectedResponseError)
