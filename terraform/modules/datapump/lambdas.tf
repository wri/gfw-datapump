resource "aws_lambda_function" "dispatcher" {
  function_name    = substr("${local.project}-dispatcher${local.name_suffix}", 0, 64)
  filename         = data.archive_file.lambda_dispatcher.output_path
  source_code_hash = data.archive_file.lambda_dispatcher.output_base64sha256
  role             = aws_iam_role.datapump_lambda.arn
  runtime          = var.lambda_dispatcher.runtime
  handler          = "lambda_function.handler"
  memory_size      = var.lambda_dispatcher.memory_size
  timeout          = var.lambda_dispatcher.timeout
  publish          = true
  tags             = local.tags
  layers           = [module.lambda_layers.datapump_arn, var.rasterio_lambda_layer_arn]
  environment {
    variables = {
      ENV                           = var.environment
      DATA_API_URI                  = var.data_api_uri
      S3_BUCKET_DATA_LAKE           = var.data_lake_bucket
      DATAPUMP_DB_S3_PATH           = local.config_db_s3_path
      S3_GLAD_PATH                  = var.glad_path
    }
  }
}

resource "aws_lambda_function" "analyzer" {
  function_name    = substr("${local.project}-analyzer${local.name_suffix}", 0, 64)
  filename         = data.archive_file.lambda_analyzer.output_path
  source_code_hash = data.archive_file.lambda_analyzer.output_base64sha256
  role             = aws_iam_role.datapump_lambda.arn
  runtime          = var.lambda_analyzer.runtime
  handler          = "lambda_function.handler"
  memory_size      = var.lambda_analyzer.memory_size
  timeout          = var.lambda_analyzer.timeout
  publish          = true
  tags             = local.tags
  layers           = [module.lambda_layers.datapump_arn]
  environment {
    variables = {
      ENV                            = var.environment
      S3_BUCKET_PIPELINE             = var.pipelines_bucket
      GEOTRELLIS_JAR_PATH            = var.geotrellis_jar_path
      PUBLIC_SUBNET_IDS              = jsonencode(var.public_subnet_ids)
      EC2_KEY_NAME                   = var.ec2_key_name
      EMR_SERVICE_ROLE               = var.emr_service_role_name
      EMR_INSTANCE_PROFILE           = var.emr_instance_profile_name
    }
  }
}

resource "aws_lambda_function" "uploader" {
  function_name    = substr("${local.project}-uploader${local.name_suffix}", 0, 64)
  filename         = data.archive_file.lambda_uploader.output_path
  source_code_hash = data.archive_file.lambda_uploader.output_base64sha256
  role             = aws_iam_role.datapump_lambda.arn
  runtime          = var.lambda_uploader.runtime
  handler          = "lambda_function.handler"
  memory_size      = var.lambda_uploader.memory_size
  timeout          = var.lambda_uploader.timeout
  publish          = true
  tags             = local.tags
  layers           = [module.lambda_layers.datapump_arn]
  environment {
    variables = {
      ENV                            = var.environment
      S3_BUCKET_PIPELINE             = var.pipelines_bucket
      DATA_API_URI                   = var.data_api_uri
    }
  }
}

resource "aws_lambda_function" "postprocessor" {
  function_name    = substr("${local.project}-postprocessor${local.name_suffix}", 0, 64)
  filename         = data.archive_file.lambda_postprocessor.output_path
  source_code_hash = data.archive_file.lambda_postprocessor.output_base64sha256
  role             = aws_iam_role.datapump_lambda.arn
  runtime          = var.lambda_postprocessor.runtime
  handler          = "lambda_function.handler"
  memory_size      = var.lambda_postprocessor.memory_size
  timeout          = var.lambda_postprocessor.timeout
  publish          = true
  tags             = local.tags
  layers           = [module.lambda_layers.datapump_arn, var.rasterio_lambda_layer_arn]
  environment {
    variables = {
      ENV                            = var.environment
      S3_BUCKET_PIPELINE             = var.pipelines_bucket
      S3_BUCKET_DATA_LAKE           = var.data_lake_bucket
      DATA_API_URI                   = var.data_api_uri
      DATAPUMP_DB_S3_PATH           = local.config_db_s3_path
    }
  }
}