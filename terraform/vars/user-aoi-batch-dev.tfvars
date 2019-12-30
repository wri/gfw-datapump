environment = "dev"

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

geotrellis_jar = "s3://gfw-pipelines-dev/geotrellis/jars/treecoverloss-assembly-1.0.0-pre-f9b5a906a62d4ee09598d862abf418bed88277b1.jar"

aoi_datasets = {
  "annualupdate_minimal": {
    "change" = "206938be-12d9-47b7-9865-44244bfb64d6"
    "summary" = "0eead72d-1ad7-4c0f-93c4-793a07cd2e3d"
    "whitelist" = "2508ebe7-ee26-4ddd-aeb1-d7e6d2772ccb"
  }
  "gladalerts": {
    "daily_alerts" = "722d90b2-e989-48ca-ba27-f7a8e236ea44"
    "weekly_alerts" = "153a2ba7-cff6-4b06-bd76-279271c4ddea"
    "summary" = "28e44bd2-cd13-4587-9259-1ba235a82d28"
    "whitelist"     = "cc0a64f1-a656-42f0-9383-7f1b68b4e46b"
  }
}