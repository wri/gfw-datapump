resource "aws_lambda_layer_version" "geotrellis_summary_update" {
  layer_name          = "geotrellis_summary_update"
  filename            = local.lambda_layer_geotrellis_summary_update
  source_code_hash    = filebase64sha256(local.lambda_layer_geotrellis_summary_update)
  compatible_runtimes = [var.lambda_submit_job_runtime]
}

resource "aws_lambda_layer_version" "shaply_pyyaml" {
  layer_name          = "shaply_pyyaml"
  filename            = local.lambda_layer_shaply_pyyaml
  source_code_hash    = filebase64sha256(local.lambda_layer_shaply_pyyaml)
  compatible_runtimes = [var.lambda_submit_job_runtime]
}

resource "aws_lambda_function" "submit_job" {
  function_name    = "submit-job_geotrellis-summary-update${local.name_suffix}"
  filename         = data.archive_file.lambda_submit_job.output_path
  source_code_hash = data.archive_file.lambda_submit_job.output_base64sha256
  role             = aws_iam_role.geotrellis_summary_update_lambda.arn
  runtime          = var.lambda_submit_job_runtime
  handler          = "lambda_function.handler"
  memory_size      = var.lambda_submit_job_memory_size
  timeout          = var.lambda_submit_job_timeout
  publish          = true
  tags             = local.tags
  layers           = [aws_lambda_layer_version.geotrellis_summary_update.arn]
  environment {
    variables = {
      ENV                = var.environment
      S3_BUCKET_PIPELINE = data.terraform_remote_state.core.outputs.pipelines_bucket
      GEOTRELLIS_JAR     = var.geotrellis_jar
    }
  }
}

resource "aws_lambda_function" "upload_results_to_datasets" {
  function_name    = "upload-results-to-datasets_geotrellis-summary-update${local.name_suffix}"
  filename         = data.archive_file.lambda_upload_results_to_datasets.output_path
  source_code_hash = data.archive_file.lambda_upload_results_to_datasets.output_base64sha256
  role             = aws_iam_role.geotrellis_summary_update_lambda.arn
  runtime          = var.lambda_upload_results_runtime
  handler          = "lambda_function.handler"
  memory_size      = var.lambda_upload_results_memory_size
  timeout          = var.lambda_upload_results_timeout
  publish          = true
  tags             = local.tags
  layers           = [aws_lambda_layer_version.geotrellis_summary_update.arn]
  environment {
    variables = {
      ENV = var.environment
    }
  }
}

resource "aws_lambda_function" "check_datasets_saved" {
  function_name    = "check-datasets-saved_geotrellis-summary-update${local.name_suffix}"
  filename         = data.archive_file.lambda_check_datasets_saved.output_path
  source_code_hash = data.archive_file.lambda_check_datasets_saved.output_base64sha256
  role             = aws_iam_role.geotrellis_summary_update_lambda.arn
  runtime          = var.lambda_check_datasets_runtime
  handler          = "lambda_function.handler"
  memory_size      = var.lambda_check_datasets_memory_size
  timeout          = var.lambda_check_datasets_timeout
  publish          = true
  tags             = local.tags
  layers           = [aws_lambda_layer_version.geotrellis_summary_update.arn]
  environment {
    variables = {
      ENV = var.environment
    }
  }
}

resource "aws_lambda_function" "check_new_areas" {
  function_name    = "check-new-areas_geotrellis-summary-update${local.name_suffix}"
  filename         = data.archive_file.lambda_check_new_areas.output_path
  source_code_hash = data.archive_file.lambda_check_new_areas.output_base64sha256
  role             = aws_iam_role.geotrellis_summary_update_lambda.arn
  runtime          = var.lambda_check_new_areas_runtime
  handler          = "lambda_function.handler"
  memory_size      = var.lambda_check_new_areas_memory_size
  timeout          = var.lambda_check_new_areas_timeout
  publish          = true
  tags             = local.tags
  layers           = [aws_lambda_layer_version.geotrellis_summary_update.arn, aws_lambda_layer_version.shaply_pyyaml.arn]
  environment {
    variables = {
      ENV                = var.environment
      S3_BUCKET_PIPELINE = data.terraform_remote_state.core.outputs.pipelines_bucket
      S3_BUCKET_DATALAKE = data.terraform_remote_state.core.outputs.data-lake_bucket
    }
  }
}

resource "aws_lambda_function" "update_new_area_statuses" {
  function_name    = "update-new-area-statuses_geotrellis-summary-update${local.name_suffix}"
  filename         = data.archive_file.lambda_update_new_area_statuses.output_path
  source_code_hash = data.archive_file.lambda_update_new_area_statuses.output_base64sha256
  role             = aws_iam_role.geotrellis_summary_update_lambda.arn
  runtime          = var.lambda_update_new_area_statuses_runtime
  handler          = "lambda_function.handler"
  memory_size      = var.lambda_update_new_area_statuses_memory_size
  timeout          = var.lambda_update_new_area_statuses_timeout
  publish          = true
  tags             = local.tags
  layers           = [aws_lambda_layer_version.geotrellis_summary_update.arn]
  environment {
    variables = {
      ENV                = var.environment
      S3_BUCKET_PIPELINE = data.terraform_remote_state.core.outputs.pipelines_bucket
    }
  }
}