# Download any stable version in AWS provider of 2.36.1000 or higher in 2.36 train
terraform {
  required_version = ">=0.12.13"
}

provider "aws" {
  region = "us-east-1"
  skip_credentials_validation = true
  skip_requesting_account_id = true
  skip_metadata_api_check = true
  s3_force_path_style = true
  endpoints {
    s3 = "http://localhost:4566"
    iam = "http://localhost:4566"
    stepfunctions = "http://localhost:4566"
    lambda = "http://localhost:4566"
    cloudwatch = "http://localhost:4566"
    sts = "http://localhost:4566"
    cloudwatchevents = "http://localhost:4566"
  }
}

module "datapump" {
  source = "../../terraform/modules/datapump"
  environment = var.environment
  policies_path = var.policies_path
  step_functions_path = var.step_functions_path
  lambdas_path = var.lambdas_path
  lambda_layers_path = var.lambda_layers_path
  geotrellis_jar = var.geotrellis_jar
  lambda_analyzer_memory_size = var.lambda_analyzer_memory_size
  lambda_analyzer_runtime = var.lambda_analyzer_runtime
  lambda_analyzer_timeout = var.lambda_analyzer_timeout
  lambda_uploader_memory_size = var.lambda_uploader_memory_size
  lambda_uploader_runtime = var.lambda_uploader_runtime
  lambda_uploader_timeout = var.lambda_analyzer_timeout
  pipelines_bucket = aws_s3_bucket.pipelines_test.id
  tags = {}
}