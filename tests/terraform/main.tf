terraform {
  required_version = ">=0.13"
}

provider "aws" {
  region = "us-east-1"
  skip_credentials_validation = true
  skip_requesting_account_id = true
  skip_metadata_api_check = true
  s3_force_path_style = true
  endpoints {
    s3 = "http://localstack:4566"
    iam = "http://localstack:4566"
    stepfunctions = "http://localstack:4566"
    lambda = "http://localstack:4566"
    cloudwatch = "http://localstack:4566"
    sts = "http://localstack:4566"
    cloudwatchevents = "http://localstack:4566"
    secretsmanager = "http://localstack:4566"
    dynamodb = "http://localstack:4566"
    apigateway = "http://localstack:4566"
  }
}

module "datapump" {
  source = "../../terraform/modules/datapump"
  environment = var.environment
  policies_path = var.policies_path
  step_functions_path = var.step_functions_path
  lambdas_path = var.lambdas_path
  lambda_layers_path = var.lambda_layers_path
  geotrellis_jar_path = var.geotrellis_jar_path
  pipelines_bucket = aws_s3_bucket.pipelines_test.id
  tags = {}
  fastapi_lambda_layer_arn = aws_lambda_layer_version.fastapi.arn
  rasterio_lambda_layer_arn = aws_lambda_layer_version.rasterio.arn
  sfn_wait_time = 1
  data_api_uri = var.data_api_uri
  data_lake_bucket = aws_s3_bucket.data_lake_test.id
  glad_path = var.glad_path
  command_runner_jar = "s3://gfw-pipelines-test/geotrellis-mock.jar"
  read_gfw_api_secrets_policy = module.api_token_secret.read_policy_arn
  read_gfw_sync_secrets_policy = module.slack_secret.read_policy_arn
}