environment = "production"

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

geotrellis_jar = "s3://gfw-pipelines-staging/geotrellis/jars/treecoverloss-assembly-1.0.3.jar"

datasets = {
  "geostore": {
    "annualupdate_minimal": {
      "change" = "d1ced422-7cd5-480a-8904-d3410d75bf42"
      "summary" = "f499105d-cf3d-4553-987a-32924512bcbf"
      "whitelist" = "d4e84309-2fd7-4397-bc2e-13db8b752462"
    }
    "gladalerts": {
      "daily_alerts" = "69f279f5-c5e3-4856-bd8b-2b5eceaef56a"
      "weekly_alerts" = "633e64ff-27d3-4203-942b-c7a93e632b45"
      "summary" = "2a22a8fc-5260-446e-b1f1-3695e325af7d"
      "whitelist" = "b4f6dd8e-d8f4-4de3-ad67-441ea6d15977"
    }
  }
  "gadm": {
    "gladalerts": {
      "iso": {
        "weekly_alerts" = "06262d5b-9e77-4f69-b979-d8524e4a90ae"
      }
      "adm1": {
        "weekly_alerts" = "ebcf3d10-beee-4d50-a517-6b3e8949ef6f"
      }
      "adm2": {
        "daily_alerts" = "61170ad0-9d6a-4347-8e58-9b551eeb341e",
        "weekly_alerts" = "2a2dd975-9d3d-4c64-b867-68756b93079f"
      }
    }
  }
  "wdpa": {
    "gladalerts": {
      "daily_alerts" = "bb2a69f1-c3ca-44e3-bd3c-0d6b9fb30169",
      "weekly_alerts" = "00732163-e34b-458f-9f5d-8c8857a6a886"
    }
  }
}