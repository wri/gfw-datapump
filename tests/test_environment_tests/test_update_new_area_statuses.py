import os

from datapump_utils.exceptions import UnexpectedResponseError
from datapump_utils.util import api_prefix
from datapump_utils.dataset import update_aoi_statuses, _update_aoi_statuses_payload

from lambdas.update_new_aoi_statuses.src.lambda_function import get_aoi_geostore_ids
from tests.mock_environment.mock_responses import TEST_ERROR_RESPONSE

os.environ["ENV"] = "test"
job_flow_id = "TESTID"


def test_update_aoi_status(requests_mock):
    geostore_ids = ["test1", "test2"]

    payload = _update_aoi_statuses_payload(geostore_ids, "saved")
    assert payload["geostores"] == geostore_ids
    assert payload["update_params"]["status"] == "saved"

    url = f"https://{api_prefix()}-api.globalforestwatch.org/v2/area/update"

    status_code = 200
    requests_mock.post(url, status_code=status_code)
    result = update_aoi_statuses(geostore_ids, "saved")
    assert result == status_code

    status_code = 500
    try:
        requests_mock.post(url, status_code=status_code, json=TEST_ERROR_RESPONSE)
        update_aoi_statuses(geostore_ids, "saved")
    except Exception as e:
        assert isinstance(e, UnexpectedResponseError)


def test_get_aoi_geostore_ids():
    aoi_src = "s3://gfw-pipelines-test/geotrellis/features/geostore/test_areas.tsv"
    result = get_aoi_geostore_ids(aoi_src)

    assert len(result) == 34
