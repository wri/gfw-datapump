environment           = "dev"

lambda_submit_job_runtime     = "python3.7"
lambda_submit_job_memory_size = 1024
lambda_submit_job_timeout     = 300

lambda_upload_results_runtime     = "python3.7"
lambda_upload_results_memory_size = 1024
lambda_upload_results_timeout     = 300

lambda_check_datasets_runtime     = "python3.7"
lambda_check_datasets_memory_size = 1024
lambda_check_datasets_timeout     = 300

lambda_check_new_areas_runtime     = "python3.7"
lambda_check_new_areas_memory_size = 1024
lambda_check_new_areas_timeout     = 300

lambda_update_new_area_statuses_runtime     = "python3.7"
lambda_update_new_area_statuses_memory_size = 1024
lambda_update_new_area_statuses_timeout     =  300

geotrellis_jar = "s3://gfw-pipelines-dev/geotrellis/jars/treecoverloss-assembly-1.0.0-pre-e63f58ebf332741f9cde986a2f2e98f63ef8bda3.jar"