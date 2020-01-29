data "archive_file" "lambda_check_datasets_saved" {
  type        = "zip"
  source_dir  = "../lambdas/check_datasets_saved/src"
  output_path = "../lambdas/check_datasets_saved/lambda.zip"
}

data "archive_file" "lambda_check_new_aoi" {
  type        = "zip"
  source_dir  = "../lambdas/check_new_aoi/src"
  output_path = "../lambdas/check_new_aoi/lambda.zip"
}

data "archive_file" "lambda_submit_job" {
  type        = "zip"
  source_dir  = "../lambdas/submit_job/src"
  output_path = "../lambdas/submit_job/lambda.zip"
}

data "archive_file" "lambda_update_new_aoi_statuses" {
  type        = "zip"
  source_dir  = "../lambdas/update_new_aoi_statuses/src"
  output_path = "../lambdas/update_new_aoi_statuses/lambda.zip"
}

data "archive_file" "lambda_upload_results_to_datasets" {
  type        = "zip"
  source_dir  = "../lambdas/upload_results_to_datasets/src"
  output_path = "../lambdas/upload_results_to_datasets/lambda.zip"
}

data "archive_file" "lambda_check_new_glad_alerts" {
  type        = "zip"
  source_dir  = "../lambdas/check_new_glad_alerts/src"
  output_path = "../lambdas/check_new_glad_alerts/lambda.zip"
}

data "archive_file" "lambda_get_latest_fire_alerts" {
  type        = "zip"
  source_dir  = "../lambdas/get_latest_fire_alerts/src"
  output_path = "../lambdas/get_latest_fire_alerts/lambda.zip"
}