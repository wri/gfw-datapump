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
  layers           = [module.lambda_layers.datapump_arn]
  environment {
    variables = {
      ENV                           = var.environment
      DATA_API_URI                  = var.data_api_uri
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
//
//resource "aws_lambda_permission" "allow_cloudwatch" {
//  statement_id  = "AllowExecutionFromCloudWatch"
//  action        = "lambda:InvokeFunction"
//  function_name = aws_lambda_function.get_latest_fire_alerts.function_name
//  principal     = "events.amazonaws.com"
//  source_arn    = aws_cloudwatch_event_rule.everyday-11-pm-est.arn
//}