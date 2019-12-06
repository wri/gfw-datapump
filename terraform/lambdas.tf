resource "aws_lambda_function" "submit_job" {
  function_name    = "submit-job_geotrellis-summary-update"
  filename         = local.lambda_submit_job_file
  source_code_hash = filebase64sha256(local.lambda_submit_job_file)
  role             = aws_iam_role.geotrellis_summary_update_lambda.arn
  runtime          = var.lambda_submit_job_runtime
  handler          = "function.handler"
  memory_size      = var.lambda_submit_job_memory_size
  timeout          = var.lambda_submit_job_timeout
  publish          = true
  tags             = local.tags
  environment {
    variables = {
      ENV                = var.environment
      S3_BUCKET_PIPELINE = data.terraform_remote_state.core.outputs.pipelines_bucket
    }
  }
}

resource "aws_lambda_function" "upload_results_to_datasets" {
  function_name    = "upload-results-to-datasets_geotrellis-summary-update"
  filename         = local.lambda_upload_results_file
  source_code_hash = filebase64sha256(local.lambda_upload_results_file)
  role             = aws_iam_role.geotrellis_summary_update_lambda.arn
  runtime          = var.lambda_upload_results_runtime
  handler          = "function.handler"
  memory_size      = var.lambda_upload_results_memory_size
  timeout          = var.lambda_upload_results_timeout
  publish          = true
  tags             = local.tags
  environment {
    variables = {
      ENV = var.environment
    }
  }
}

resource "aws_lambda_function" "check_datasets_saved" {
  function_name    = "check-datasets-saved_geotrellis-summary-update"
  filename         = local.lambda_check_dataset_file
  source_code_hash = filebase64sha256(local.lambda_check_dataset_file)
  role             = aws_iam_role.geotrellis_summary_update_lambda.arn
  runtime          = var.lambda_check_datasets_runtime
  handler          = "function.handler"
  memory_size      = var.lambda_check_datasets_memory_size
  timeout          = var.lambda_check_datasets_timeout
  publish          = true
  tags             = local.tags
  environment {
    variables = {
      ENV = var.environment
    }
  }
}

resource "aws_lambda_function" "check_new_areas" {
  function_name    = "check-new-areas_geotrellis-summary-update"
  filename         = local.lambda_check_new_area_file
  source_code_hash = filebase64sha256(local.lambda_check_new_area_file)
  role             = aws_iam_role.geotrellis_summary_update_lambda.arn
  runtime          = var.lambda_check_new_areas_runtime
  handler          = "function.handler"
  memory_size      = var.lambda_check_new_areas_memory_size
  timeout          = var.lambda_check_new_areas_timeout
  publish          = true
  tags             = local.tags
  environment {
    variables = {
      ENV                = var.environment
      S3_BUCKET_PIPELINE = data.terraform_remote_state.core.outputs.pipelines_bucket
      S3_BUCKET_DATALAKE = data.terraform_remote_state.core.outputs.data-lake_bucket
    }
  }
}

resource "aws_lambda_function" "update_new_area_statuses" {
  function_name    = "update-new-area-statuses_geotrellis-summary-update"
  filename         = local.lambda_update_new_area_statuses_file
  source_code_hash = filebase64sha256(local.lambda_update_new_area_statuses_file)
  role             = aws_iam_role.geotrellis_summary_update_lambda.arn
  runtime          = var.lambda_update_new_area_statuses_runtime
  handler          = "function.handler"
  memory_size      = var.lambda_update_new_area_statuses_memory_size
  timeout          = var.lambda_update_new_area_statuses_timeout
  publish          = true
  tags             = local.tags
  environment {
    variables = {
      ENV                = var.environment
      S3_BUCKET_PIPELINE = data.terraform_remote_state.core.outputs.pipelines_bucket
    }
  }
}