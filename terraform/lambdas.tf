resource "aws_lambda_function" "submit_job" {
  function_name    = substr("${local.project}-submit_job${local.name_suffix}", 0, 64)
  filename         = data.archive_file.lambda_submit_job.output_path
  source_code_hash = data.archive_file.lambda_submit_job.output_base64sha256
  role             = aws_iam_role.datapump_lambda.arn
  runtime          = var.lambda_submit_job_runtime
  handler          = "lambda_function.handler"
  memory_size      = var.lambda_submit_job_memory_size
  timeout          = var.lambda_submit_job_timeout
  publish          = true
  tags             = local.tags
  layers           = [module.lambda_layers.datapump_utils_arn]
  environment {
    variables = {
      ENV                            = var.environment
      S3_BUCKET_PIPELINE             = data.terraform_remote_state.core.outputs.pipelines_bucket
      GEOTRELLIS_JAR                 = var.geotrellis_jar
      PUBLIC_SUBNET_IDS              = jsonencode(data.terraform_remote_state.core.outputs.public_subnet_ids)
      EC2_KEY_NAME                   = data.terraform_remote_state.core.outputs.key_pair_tmaschler_gfw
      EMR_SERVICE_ROLE               = data.terraform_remote_state.core.outputs.emr_service_role_name
      EMR_INSTANCE_PROFILE           = data.terraform_remote_state.core.outputs.emr_instance_profile_name
    }
  }
}

resource "aws_lambda_function" "upload_results_to_datasets" {
  function_name    = substr("${local.project}-upload_results_to_datasets${local.name_suffix}", 0, 64)
  filename         = data.archive_file.lambda_upload_results_to_datasets.output_path
  source_code_hash = data.archive_file.lambda_upload_results_to_datasets.output_base64sha256
  role             = aws_iam_role.datapump_lambda.arn
  runtime          = var.lambda_upload_results_runtime
  handler          = "lambda_function.handler"
  memory_size      = var.lambda_upload_results_memory_size
  timeout          = var.lambda_upload_results_timeout
  publish          = true
  tags             = local.tags
  layers           = [module.lambda_layers.datapump_utils_arn]
  environment {
    variables = {
      ENV                            = var.environment
      S3_BUCKET_PIPELINE             = data.terraform_remote_state.core.outputs.pipelines_bucket
      PUBLIC_SUBNET_IDS              = jsonencode(data.terraform_remote_state.core.outputs.public_subnet_ids)
      EC2_KEY_NAME                   = data.terraform_remote_state.core.outputs.key_pair_tmaschler_gfw
    }
  }
}

resource "aws_lambda_function" "check_datasets_saved" {
  function_name    = substr("${local.project}-check_datasets_saved${local.name_suffix}", 0, 64)
  filename         = data.archive_file.lambda_check_datasets_saved.output_path
  source_code_hash = data.archive_file.lambda_check_datasets_saved.output_base64sha256
  role             = aws_iam_role.datapump_lambda.arn
  runtime          = var.lambda_check_datasets_runtime
  handler          = "lambda_function.handler"
  memory_size      = var.lambda_check_datasets_memory_size
  timeout          = var.lambda_check_datasets_timeout
  publish          = true
  tags             = local.tags
  layers           = [module.lambda_layers.datapump_utils_arn]
  environment {
    variables = {
      ENV = var.environment
      S3_BUCKET_PIPELINE             = data.terraform_remote_state.core.outputs.pipelines_bucket
      PUBLIC_SUBNET_IDS              = jsonencode(data.terraform_remote_state.core.outputs.public_subnet_ids)
      EC2_KEY_NAME                   = data.terraform_remote_state.core.outputs.key_pair_tmaschler_gfw
    }
  }
}

resource "aws_lambda_function" "check_new_aoi" {
  function_name    = substr("${local.project}-check_new_aoi${local.name_suffix}", 0, 64)
  filename         = data.archive_file.lambda_check_new_aoi.output_path
  source_code_hash = data.archive_file.lambda_check_new_aoi.output_base64sha256
  role             = aws_iam_role.datapump_lambda.arn
  runtime          = var.lambda_check_new_aoi_runtime
  handler          = "lambda_function.handler"
  memory_size      = var.lambda_check_new_aoi_memory_size
  timeout          = var.lambda_check_new_aoi_timeout
  publish          = true
  tags             = local.tags
  layers           = [module.lambda_layers.datapump_utils_arn, data.terraform_remote_state.lambda-layers.outputs.py37_shapely_164_arn]
  environment {
    variables = {
      ENV                = var.environment
      S3_BUCKET_PIPELINE = data.terraform_remote_state.core.outputs.pipelines_bucket
      S3_BUCKET_DATALAKE = data.terraform_remote_state.core.outputs.data-lake_bucket
      DATASETS    = jsonencode(var.datasets)
    }
  }
}

resource "aws_lambda_function" "update_new_aoi_statuses" {
  function_name    = substr("${local.project}-update_new_aoi_statuses${local.name_suffix}", 0, 64)
  filename         = data.archive_file.lambda_update_new_aoi_statuses.output_path
  source_code_hash = data.archive_file.lambda_update_new_aoi_statuses.output_base64sha256
  role             = aws_iam_role.datapump_lambda.arn
  runtime          = var.lambda_update_new_aoi_statuses_runtime
  handler          = "lambda_function.handler"
  memory_size      = var.lambda_update_new_aoi_statuses_memory_size
  timeout          = var.lambda_update_new_aoi_statuses_timeout
  publish          = true
  tags             = local.tags
  layers           = [module.lambda_layers.datapump_utils_arn]
  environment {
    variables = {
      ENV                = var.environment
      S3_BUCKET_PIPELINE = data.terraform_remote_state.core.outputs.pipelines_bucket
    }
  }
}

resource "aws_lambda_function" "check_new_glad_alerts" {
  function_name    = substr("${local.project}-check_new_glad_alerts${local.name_suffix}",0, 64)
  filename         = data.archive_file.lambda_check_new_glad_alerts.output_path
  source_code_hash = data.archive_file.lambda_check_new_glad_alerts.output_base64sha256
  role             = aws_iam_role.datapump_lambda.arn
  runtime          = var.lambda_check_new_glad_alerts_runtime
  handler          = "lambda_function.handler"
  memory_size      = var.lambda_check_new_glad_alerts_memory_size
  timeout          = var.lambda_check_new_glad_alerts_timeout
  publish          = true
  tags             = local.tags
  layers           = [module.lambda_layers.datapump_utils_arn]
  environment {
    variables = {
      ENV                = var.environment
      S3_BUCKET_PIPELINE = data.terraform_remote_state.core.outputs.pipelines_bucket
      DATASETS       = jsonencode(var.datasets)
      GLAD_STATUS_PATH   = "s3://gfw2-data/forest_change/umd_landsat_alerts/prod/events/status"
    }
  }
}

resource "aws_lambda_function" "get_latest_fire_alerts" {
  function_name    = substr("${local.project}-get_latest_fire_alerts${local.name_suffix}",0, 64)
  filename         = data.archive_file.lambda_get_latest_fire_alerts.output_path
  source_code_hash = data.archive_file.lambda_get_latest_fire_alerts.output_base64sha256
  role             = aws_iam_role.datapump_lambda.arn
  runtime          = var.lambda_get_latest_fire_alerts_runtime
  handler          = "lambda_function.handler"
  memory_size      = var.lambda_get_latest_fire_alerts_memory_size
  timeout          = var.lambda_get_latest_fire_alerts_timeout
  publish          = true
  tags             = local.tags
  layers           = [module.lambda_layers.datapump_utils_arn, data.terraform_remote_state.lambda-layers.outputs.py37_rasterio_115_arn]
  environment {
    variables = {
      ENV                 = var.environment
      S3_BUCKET_DATA_LAKE = data.terraform_remote_state.core.outputs.data-lake_bucket
      S3_BUCKET_PIPELINE  = data.terraform_remote_state.core.outputs.pipelines_bucket
      DATASETS            = jsonencode(var.datasets)
    }
  }
}

resource "aws_lambda_function" "inject_fires_data" {
  function_name    = substr("${local.project}-inject_fires_data${local.name_suffix}", 0, 64)
  filename         = data.archive_file.lambda_inject_fires_data.output_path
  source_code_hash = data.archive_file.lambda_inject_fires_data.output_base64sha256
  role             = aws_iam_role.datapump_lambda.arn
  runtime          = var.lambda_update_new_aoi_statuses_runtime
  handler          = "lambda_function.handler"
  memory_size      = var.lambda_update_new_aoi_statuses_memory_size
  timeout          = var.lambda_update_new_aoi_statuses_timeout
  publish          = true
  tags             = local.tags
  layers           = [module.lambda_layers.datapump_utils_arn]
  environment {
    variables = {
      ENV                = var.environment
      DATA_API_VIIRS_VERSION = var.data_api_viirs_version
      S3_BUCKET_PIPELINE             = data.terraform_remote_state.core.outputs.pipelines_bucket
      PUBLIC_SUBNET_IDS              = jsonencode(data.terraform_remote_state.core.outputs.public_subnet_ids)
      EC2_KEY_NAME                   = data.terraform_remote_state.core.outputs.key_pair_tmaschler_gfw
    }
  }
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_latest_fire_alerts.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.everyday-11-pm-est.arn
}