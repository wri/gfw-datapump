import csv
import geojson
import pytest
import os
from moto import mock_s3, mock_secretsmanager

from tests.mock_environment.mock_environment import mock_environment

from datapump_utils.util import get_date_string
from datapump_utils.s3 import s3_client
from datapump_utils.fire_alerts import (
    process_active_fire_alerts,
    ACTIVE_FIRE_ALERTS_24HR_CSV_URLS,
)


@mock_secretsmanager
@mock_s3
@pytest.mark.parametrize("alert_type", ["MODIS", "VIIRS"])
def test_get_active_fire_alerts(alert_type, requests_mock):
    mock_environment()

    test_response = TEST_FIRE_ALERT_RESPONSE[alert_type]
    requests_mock.get(
        url=ACTIVE_FIRE_ALERTS_24HR_CSV_URLS[alert_type], text=test_response
    )

    process_active_fire_alerts(alert_type)
    result_name = f"{alert_type}_{get_date_string()}"
    with open(f"{result_name}.tsv", "r") as tsv_result_file:
        with open(f"{result_name}.geojson", "r") as geojson_result_file:
            tsv_result = csv.DictReader(
                tsv_result_file.read().splitlines(), delimiter="\t"
            )
            expected_result = csv.DictReader(test_response.splitlines(), delimiter=",")
            geojson_result = geojson.load(geojson_result_file)

            for result_row, expected_row, feature in zip(
                tsv_result, expected_result, geojson_result.features
            ):
                assert result_row["latitude"] == expected_row["latitude"]
                assert result_row["longitude"] == expected_row["longitude"]

                assert feature.geometry.coordinates[0] == float(
                    expected_row["longitude"]
                )
                assert feature.geometry.coordinates[1] == float(
                    expected_row["latitude"]
                )

    assert s3_client().head_object(
        Bucket=os.environ["S3_BUCKET_PIPELINE"],
        Key=f"features/{alert_type}_active_fire_alerts/{result_name}.tsv",
    )
    assert s3_client().head_object(
        Bucket=os.environ["S3_BUCKET_DATA_LAKE"],
        Key=f"{alert_type}_active_fire_alerts/vector/espg-4326/{result_name}.geojson",
    )


TEST_FIRE_ALERT_RESPONSE = {
    "MODIS": """latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,confidence,version,bright_t31,frp,daynight
-27.402,147.909,331.4,1.1,1.1,2020-01-21,0030,T,53,6.0NRT,315,11.4,D
-27.412,147.907,340.4,1.1,1.1,2020-01-21,0030,T,83,6.0NRT,316.7,26.6,D
-27.413,147.918,337.6,1.1,1.1,2020-01-21,0030,T,79,6.0NRT,316.7,21.9,D
-27.415,147.93,331.7,1.1,1.1,2020-01-21,0030,T,67,6.0NRT,316.2,11.9,D
-28.234,149.859,335,1.4,1.2,2020-01-21,0030,T,81,6.0NRT,315.9,23.7,D
-28.238,149.853,331,1.4,1.2,2020-01-21,0030,T,75,6.0NRT,315.4,15.8,D
-30.807,151.412,322.6,1.9,1.4,2020-01-21,0030,T,65,6.0NRT,303.5,29.7,D
-30.809,151.432,329.9,2,1.4,2020-01-21,0030,T,78,6.0NRT,302.9,53,D
-30.362,146.945,343.9,1.1,1,2020-01-21,0030,T,87,6.0NRT,313.6,36.4,D
-30.364,146.956,337.5,1.1,1,2020-01-21,0030,T,80,6.0NRT,313.5,24.1,D
-33.006,146.297,326.6,1.1,1,2020-01-21,0030,T,24,6.0NRT,310.2,8.6,D
-33.016,146.296,337.1,1.1,1,2020-01-21,0030,T,83,6.0NRT,311,24.6,D
-33.886,142.684,341.6,1,1,2020-01-21,0030,T,87,6.0NRT,313.3,27.1,D
-33.888,142.695,354.6,1,1,2020-01-21,0030,T,96,6.0NRT,314.2,55.2,D
-33.889,142.706,357.8,1,1,2020-01-21,0030,T,98,6.0NRT,314.5,64.6,D
-37.692,145.032,317.4,1.1,1,2020-01-21,0030,T,59,6.0NRT,299.8,7.7,D
-37.696,145.025,313.6,1.1,1,2020-01-21,0030,T,46,6.0NRT,299,5.8,D
-10.025,147.827,318.9,1.1,1,2020-01-21,0025,T,49,6.0NRT,297.1,7.6,D
-10.026,147.837,319.5,1.1,1,2020-01-21,0025,T,46,6.0NRT,297.4,8,D
-19.029,146.633,312.5,1,1,2020-01-21,0025,T,27,6.0NRT,294.5,6,D
-19.469,145.6,331.6,1.1,1,2020-01-21,0025,T,75,6.0NRT,302.4,13.9,D
-19.471,145.61,340.8,1.1,1,2020-01-21,0025,T,86,6.0NRT,302,30.8,D
-19.475,145.603,333.9,1.1,1,2020-01-21,0025,T,79,6.0NRT,301.1,18,D
-19.477,145.613,330.3,1.1,1,2020-01-21,0025,T,71,6.0NRT,300.3,13.7,D
-19.351,144.597,326.5,1.2,1.1,2020-01-21,0025,T,50,6.0NRT,302.3,10.9,D
-23.623,148.66,335.3,1.1,1,2020-01-21,0025,T,86,6.0NRT,297.2,27.1,D
-23.625,148.671,333.3,1.1,1,2020-01-21,0025,T,84,6.0NRT,298.4,23.3,D
-25.647,150.53,327.4,1.5,1.2,2020-01-21,0025,T,70,6.0NRT,302.5,21.3,D
-26.062,147.095,345.1,1,1,2020-01-21,0025,T,88,6.0NRT,317.8,28.9,D
-26.095,146.798,337.9,1,1,2020-01-21,0025,T,79,6.0NRT,318.2,18.9,D
""",
    "VIIRS": """latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,confidence,version,bright_ti5,frp,daynight
65.76917,24.18936,338.9,0.43,0.38,2020-01-22,0036,N,nominal,1.0NRT,272,6,N
65.76575,24.18696,312.4,0.43,0.38,2020-01-22,0036,N,nominal,1.0NRT,269.3,6,N
65.76232,24.18457,329.4,0.43,0.38,2020-01-22,0036,N,nominal,1.0NRT,270.5,5.8,N
65.56535,22.21959,307.7,0.47,0.4,2020-01-22,0042,N,nominal,1.0NRT,269.2,2.3,N
65.55402,22.25519,330,0.47,0.39,2020-01-22,0042,N,nominal,1.0NRT,269.9,5.5,N
56.40143,41.33034,295.7,0.37,0.58,2020-01-22,0042,N,nominal,1.0NRT,270.3,0.6,N
59.2752,27.88592,301.7,0.4,0.37,2020-01-22,0042,N,nominal,1.0NRT,271.6,0.8,N
60.80533,1.44585,314.4,0.58,0.7,2020-01-22,0042,N,nominal,1.0NRT,275.7,2.6,N
60.13363,15.42122,303.5,0.39,0.44,2020-01-22,0042,N,nominal,1.0NRT,271.2,0.8,N
58.35916,12.37974,298.2,0.47,0.48,2020-01-22,0042,N,nominal,1.0NRT,274.1,0.6,N
58.08508,11.82646,355.6,0.49,0.49,2020-01-22,0042,N,nominal,1.0NRT,276.3,11.4,N
58.08558,11.8179,304.4,0.49,0.49,2020-01-22,0042,N,nominal,1.0NRT,274.6,6.1,N
57.06064,9.97395,302.2,0.56,0.52,2020-01-22,0042,N,nominal,1.0NRT,268.1,1.9,N
57.0619,9.97555,305.9,0.56,0.52,2020-01-22,0042,N,nominal,1.0NRT,269.1,1.6,N
53.57033,-0.59705,322.3,0.71,0.75,2020-01-22,0042,N,nominal,1.0NRT,275.2,3.3,N
53.397,-1.3877,319.5,0.76,0.77,2020-01-22,0042,N,nominal,1.0NRT,273.8,2.9,N
53.39651,-1.39242,321.2,0.76,0.77,2020-01-22,0042,N,nominal,1.0NRT,274.2,4.1,N
51.1042,18.9431,301.6,0.39,0.36,2020-01-22,0042,N,nominal,1.0NRT,272.3,1.6,N
49.88803,24.74233,323.2,0.45,0.39,2020-01-22,0042,N,nominal,1.0NRT,269.9,3,N
49.88648,24.74154,326.6,0.45,0.39,2020-01-22,0042,N,nominal,1.0NRT,269.7,2.6,N
49.8877,24.73541,297.4,0.45,0.39,2020-01-22,0042,N,nominal,1.0NRT,269.6,0.7,N
51.17791,16.11321,340.7,0.45,0.39,2020-01-22,0042,N,nominal,1.0NRT,273.8,10.3,N""",
}
