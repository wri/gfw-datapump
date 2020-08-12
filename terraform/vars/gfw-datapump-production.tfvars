environment = "production"

lambda_submit_job_runtime     = "python3.7"
lambda_submit_job_memory_size = 1024
lambda_submit_job_timeout     = 300

lambda_upload_results_runtime     = "python3.7"
lambda_upload_results_memory_size = 1024
lambda_upload_results_timeout     = 300

lambda_check_datasets_runtime     = "python3.7"
lambda_check_datasets_memory_size = 1024
lambda_check_datasets_timeout     = 300

lambda_check_new_aoi_runtime     = "python3.7"
lambda_check_new_aoi_memory_size = 3008
lambda_check_new_aoi_timeout     = 900

lambda_update_new_aoi_statuses_runtime     = "python3.7"
lambda_update_new_aoi_statuses_memory_size = 3008
lambda_update_new_aoi_statuses_timeout     = 900

lambda_check_new_glad_alerts_runtime     = "python3.7"
lambda_check_new_glad_alerts_memory_size = 1024
lambda_check_new_glad_alerts_timeout     = 300

lambda_get_latest_fire_alerts_runtime     = "python3.6"
lambda_get_latest_fire_alerts_memory_size = 3008
lambda_get_latest_fire_alerts_timeout     = 900

data_api_viirs_version = "v202008.3"

geotrellis_jar = "s3://gfw-pipelines/geotrellis/jars/treecoverloss-assembly-1.1.3.jar"

datasets = {
  "geostore": {
    "annualupdate_minimal": {
      "change" = "ecb4817b-a09e-4c78-b735-617e93a7ff4c"
      "summary" = "b2603f43-8349-4401-99d3-2fb56f889388"
      "whitelist" = "28006d70-42b5-4034-9008-505806101863"
    }
    "gladalerts": {
      "daily_alerts" = "bd35ab8e-1810-4eda-981e-5f0e6fe76f74"
      "weekly_alerts" = "95735f8d-b86b-485a-8766-c480dd4da21d"
      "summary" = "11454c79-e0ac-4c58-90ee-dcc9d9d30031"
      "whitelist" = "61d9f9bc-883c-4c70-865a-af8126c7ccee"
    }
    "firealerts_modis": {
      "daily_alerts" = "b7bf28ef-e893-47da-844a-25a46115fe34"
      "weekly_alerts" = "1f7bb181-7b28-4823-8aa5-28335268f961"
      "whitelist" = "d7d9a4b0-e295-42a8-bd46-fb48981c1eca"
    }
    "firealerts_viirs": {
      "daily_alerts" = "825edfcd-07f4-4b2b-9054-282663c60caa"
      "weekly_alerts" = "cfd880fd-8b81-46c2-b3e3-84ba22955337"
      "whitelist" = "e101f15a-4104-4dfd-bade-164986154694"
    }
  }
  "gadm": {
    "gladalerts": {
      "iso": {
        "weekly_alerts" = "2c444b8d-991a-4e90-bb18-6d9063be1432"
      }
      "adm1": {
        "weekly_alerts" = "094ae08c-3bf2-4d85-830e-e6d4cbc5c05d"
      }
      "adm2": {
        "daily_alerts" = "2cacc2dc-35d6-46ab-8641-384267b8ba64",
        "weekly_alerts" = "6476cd26-446a-4bc0-add5-79baeecceb12"
      }
    }
    "firealerts_viirs": {
      "all" = "76642243-d895-48f7-b8e8-5333851bd00f"
      "iso": {
        "weekly_alerts" = "4625ce33-4046-49e3-9861-86d9b1832710"
      }
      "adm1": {
        "weekly_alerts" = "0759c142-3a10-445e-a0f8-7e2c61c23344"
      }
      "adm2": {
        "daily_alerts" = "c1bb5e10-4da9-4776-8362-ab48a746fcb5"
        "weekly_alerts" = "13b5df89-abdd-4235-9cd0-accd1c38f11a"
      }
    }
    "firealerts_modis": {
      "iso": {
        "weekly_alerts" = "9801eea9-6cbc-4d93-9845-de6fa267fbae"
      }
      "adm1": {
        "weekly_alerts" = "29aec1f5-7f76-4b44-bd4b-61fb803765ee"
      }
      "adm2": {
        "daily_alerts" = "269af948-fc1c-40d7-823b-35bdb75c67ad"
        "weekly_alerts" = "724293e5-8eac-4b7e-b7fb-e190db2633a0"
      }
    }
  }
  "wdpa": {
    "gladalerts": {
      "daily_alerts" = "bfb86d53-c8de-46c5-a424-94eb63fea6da",
      "weekly_alerts" = "8b7240e7-8372-4b6e-9aed-4694c7a46b49"
    }
    "firealerts_modis": {
      "daily_alerts" = "83b55c8f-2d0c-4002-bd8b-568593393c24"
      "weekly_alerts" = "33d2256e-645f-44cf-b0d3-2613a71cf62b"
    }
    "firealerts_viirs": {
      "daily_alerts" = "43371354-4a60-4cac-afd9-1e4627682ea2"
      "weekly_alerts" = "02f3d46b-ba14-469c-b536-4d189834d71a"
    }
  }
}