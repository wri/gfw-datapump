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
      "change" = "d67db9ab-1462-4622-b4a7-e29f403df1a5"
      "summary" = "09c2a7b5-120b-4907-a4ea-c7b62a3b252b"
      "whitelist" = "6c004b6c-c940-495d-9ba7-c952afa960ec"
    }
    "gladalerts": {
      "daily_alerts" = "0064ccfb-efb0-4bd4-befa-b2ba034197d1"
      "weekly_alerts" = "5c62a80a-7846-4dfc-b174-53285da9e37a"
      "summary" = "d78f39a4-9273-4f45-8ec4-d9665b8666d9"
      "whitelist" = "b2d07932-beff-4590-93e7-1d03cdb2d6b4"
    }
    "firealerts_modis": {
      "daily_alerts" = "5012bfdf-27a0-456e-b0cb-b4d9730b4ddf"
      "weekly_alerts" = "df929dfc-6baf-4032-8a2e-dd9b840e9142"
      "whitelist" = "b43fe0c2-25c5-4a51-b826-c6665a5c3c3a"
    }
    "firealerts_viirs": {
      "daily_alerts" = "ef91cab3-92ba-4bf4-bb3e-edd526529be2"
      "weekly_alerts" = "73f7fd7b-9e7c-4a14-be67-79c88f806b42"
      "whitelist" = "84b5f5e5-64fe-40ae-b647-9829e38cf051"
    }
  }
  "gadm": {
    "gladalerts": {
      "iso": {
        "weekly_alerts" = "e090cf7c-d52e-4511-8d54-7ff083cd5ba4"
      }
      "adm1": {
        "weekly_alerts" = "7dfccab0-7b5b-4812-926f-bdda40fd2d73"
      }
      "adm2": {
        "daily_alerts" = "591dfe99-3184-4ab5-a5b5-1efb642f1606",
        "weekly_alerts" = "9388c2dd-2b32-449f-9ce9-d31386a45d74"
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
      "daily_alerts" = "cb00f471-63d5-4531-9177-17b4c7acaccf",
      "weekly_alerts" = "325f79c1-550f-4928-97c2-c4d0904edc88"
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