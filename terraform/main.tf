# Download any stable version in AWS provider of 2.36.0 or higher in 2.36 train
terraform {
  required_version = ">=0.12.13"
  backend "s3" {
    key     = "wri__gfw_datapump.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}

provider "aws" {
  region  = "us-east-1"
  version = "~> 2.36.0"
}

data "terraform_remote_state" "core" {
  backend = "s3"
  config = {
    bucket = local.tf_state_bucket
    region = "us-east-1"
    key    = "core.tfstate"
  }
}


data "terraform_remote_state" "lambda-layers" {
  backend = "s3"
  config = {
    bucket = local.tf_state_bucket
    region = "us-east-1"
    key    = "lambda-layers.tfstate"
  }
}

module "datapump" {
  source = "./modules/datapump"
  environment = var.environment
  policies_path = var.policies_path
  step_functions_path = var.step_functions_path
  lambdas_path = var.lambdas_path
  lambda_layers_path = var.lambda_layers_path
  geotrellis_jar_path = var.geotrellis_jar_path
  pipelines_bucket = data.terraform_remote_state.core.outputs.pipelines_bucket
  tags = local.tags
  lambda_analyzer = var.lambda_analyzer
  lambda_dispatcher = var.lambda_dispatcher
  lambda_uploader = var.lambda_uploader
  lambda_postprocessor = var.lambda_postprocessor
  sfn_wait_time = 30
  data_api_uri = var.data_api_uri
  data_lake_bucket = data.terraform_remote_state.core.outputs.data-lake_bucket
  rasterio_lambda_layer_arn = data.terraform_remote_state.lambda-layers.outputs.py37_rasterio_115_arn
  glad_path = local.glad_path
}

locals {
  bucket_suffix               = var.environment == "production" ? "" : "-${var.environment}"
  tf_state_bucket             = "gfw-terraform${local.bucket_suffix}"
  tags                        = data.terraform_remote_state.core.outputs.tags
  name_suffix                 = "-${terraform.workspace}"
  project                     = "datapump"
  glad_path                   = "s3://gfw2-data/forest_change/umd_landsat_alerts/prod"
}