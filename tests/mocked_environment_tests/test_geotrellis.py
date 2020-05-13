from moto import mock_s3, mock_emr, mock_secretsmanager
from tests.mock_environment.mock_environment import mock_environment

from lambdas.get_latest_fire_alerts.src.lambda_function import _get_fire_emr_config


@mock_s3
@mock_emr
@mock_secretsmanager
def test_fire_emr_config():
    config = _get_fire_emr_config("test_viirs_path", "test_modis_path")
    result = config.to_serializable()
