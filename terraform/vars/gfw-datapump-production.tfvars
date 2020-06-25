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

geotrellis_jar = "s3://gfw-pipelines-staging/geotrellis/jars/treecoverloss-assembly-1.1.0.jar"

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
  }
  "wdpa": {
    "gladalerts": {
      "daily_alerts" = "cb00f471-63d5-4531-9177-17b4c7acaccf",
      "weekly_alerts" = "325f79c1-550f-4928-97c2-c4d0904edc88"
    }
  }
}