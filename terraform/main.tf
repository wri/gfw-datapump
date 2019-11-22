terraform {
  backend "s3" {
    bucket = "gfw-terraform-dev"
    key    = "state/terraform.tfstate"
    region = "us-east-1"
  }
}

resource "aws_lambda_function" "submit_batch_job" {
  function_name    = "submit-batch-job_geotrellis-summary-update"
  filename         = "../lambdas/submit_job/function.zip"
  source_code_hash = "${filebase64sha256("../lambdas/submit_job/function.zip")}"
  role             = "arn:aws:iam::563860007740:role/service-role/raster-analysis-role-7aosf9ch"
  runtime          = "python3.7"
  handler          = "function.handler"
  memory_size      = 128
  timeout          = 5
  publish          = true
}

resource "aws_lambda_function" "upload_results_to_datasets" {
  function_name    = "upload-results-to-datasets_geotrellis-summary-update"
  filename         = "../lambdas/upload_results_to_datasets/function.zip"
  source_code_hash = "${filebase64sha256("../lambdas/upload_results_to_datasets/function.zip")}"
  role             = "arn:aws:iam::563860007740:role/service-role/raster-analysis-role-7aosf9ch"
  runtime          = "python3.7"
  handler          = "function.handler"
  memory_size      = 128
  timeout          = 5
  publish          = true
}

resource "aws_lambda_function" "check_datasets_saved" {
  function_name    = "check-datasets-saved_geotrellis-summary-update"
  filename         = "../lambdas/check_datasets_saved/function.zip"
  source_code_hash = "${filebase64sha256("../lambdas/check_datasets_saved/function.zip")}"
  role             = "arn:aws:iam::563860007740:role/service-role/raster-analysis-role-7aosf9ch"
  runtime          = "python3.7"
  handler          = "function.handler"
  memory_size      = 128
  timeout          = 5
  publish          = true
}

resource "aws_sfn_state_machine" "geotrellis_summary_update" {
  name     = "geotrellis-summary-update"
  role_arn = "arn:aws:iam::563860007740:role/service-role/StepFunctionExcecution"

  definition = "${file("../step_functions/geotrellis_summary_update.json")}"
}