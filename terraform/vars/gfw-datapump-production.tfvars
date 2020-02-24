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
lambda_check_new_aoi_memory_size = 1024
lambda_check_new_aoi_timeout     = 300

lambda_update_new_aoi_statuses_runtime     = "python3.7"
lambda_update_new_aoi_statuses_memory_size = 1024
lambda_update_new_aoi_statuses_timeout     = 300

lambda_check_new_glad_alerts_runtime     = "python3.7"
lambda_check_new_glad_alerts_memory_size = 1024
lambda_check_new_glad_alerts_timeout     = 300

lambda_get_latest_fire_alerts_runtime     = "python3.7"
lambda_get_latest_fire_alerts_memory_size = 1024
lambda_get_latest_fire_alerts_timeout     = 300

geotrellis_jar = "s3://gfw-pipelines-staging/geotrellis/jars/treecoverloss-assembly-1.0.0.jar"

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
        "weekly_alerts" = "8537210d-7c96-45c6-a90d-cbdcd762bc18"
      }
      "adm1": {
        "weekly_alerts" = "47b50ffa-9a82-4ad9-94ea-5eae3e2e8209"
      }
      "adm2": {
        "daily_alerts" = "cd5c83e9-d407-491b-a41c-21a72bda9109",
        "weekly_alerts" = "795f0b0c-5822-47ec-ad08-1eafc005f9a3"
      }
    }
  }
  "wdpa": {
    "gladalerts": {
      "daily_alerts" = "5469f72e-2305-4561-ac9e-9bd6aa92a70b",
      "weekly_alerts" = "770cc7b1-1a40-47cf-8f12-978fe3ae91a2"
    }
  }
}