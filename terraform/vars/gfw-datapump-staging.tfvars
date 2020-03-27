environment = "staging"

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

lambda_get_latest_fire_alerts_runtime     = "python3.7"
lambda_get_latest_fire_alerts_memory_size = 1024
lambda_get_latest_fire_alerts_timeout     = 300

geotrellis_jar = "s3://gfw-pipelines-staging/geotrellis/jars/treecoverloss-assembly-1.0.3.jar"

datasets = {
  "geostore": {
    "annualupdate_minimal": {
      "change" = "952f3a90-ea03-4bf7-93a7-5ffbca48248d"
      "summary" = "8a857b48-971d-4358-bd91-243d248ec713"
      "whitelist" = "2508ebe7-ee26-4ddd-aeb1-d7e6d2772ccb"
    }
    "gladalerts": {
      "daily_alerts" = "23483d57-4bf7-426a-903b-b917a335eec0"
      "weekly_alerts" = "3172b978-3ef1-4e01-8943-03a4c259f12f"
      "summary" = "489a5e5d-067f-4528-9395-a20c86ed329e"
      "whitelist" = "cc0a64f1-a656-42f0-9383-7f1b68b4e46b"
    }
  }
  "gadm": {
    "gladalerts": {
      "iso": {
        "weekly_alerts" = "f79d86c8-e1f7-4611-8172-5ab029c45c8d"
      }
      "adm1": {
        "weekly_alerts" = "2c192cfd-52d2-440b-85c1-4496b7cf3de7"
      }
      "adm2": {
        "daily_alerts" = "f328893b-1a53-4d11-b00a-e6f5767db1be",
        "weekly_alerts" = "a6195a49-7d58-4284-af29-24dc7ddd627f"
      }
    }
  }
  "wdpa": {
    "gladalerts": {
      "daily_alerts" = "99b1e1ea-eea8-4212-9868-ee4b69f1b268",
      "weekly_alerts" = "7e0669c2-e35b-4fa4-9e06-7a3c8e0cd767"
    }
  }
}