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
  emr_instance_profile_name = data.terraform_remote_state.core.outputs.emr_instance_profile_name
  emr_service_role_name = data.terraform_remote_state.core.outputs.emr_service_role_name
  public_subnet_ids = data.terraform_remote_state.core.outputs.public_subnet_ids
  ec2_key_name = data.terraform_remote_state.core.outputs.key_pair_tmaschler_gfw
  read_gfw_api_secrets_policy = data.terraform_remote_state.core.outputs.secrets_read-gfw-api-token_policy_arn
  read_gfw_sync_secrets_policy = data.terraform_remote_state.core.outputs.secrets_read-slack-gfw-sync_policy_arn
}

locals {
  bucket_suffix               = var.environment == "production" ? "" : "-${var.environment}"
  tf_state_bucket             = "gfw-terraform${local.bucket_suffix}"
  tags                        = data.terraform_remote_state.core.outputs.tags
  name_suffix                 = "-${terraform.workspace}"
  project                     = "datapump"
  glad_path                   = "s3://gfw2-data/forest_change/umd_landsat_alerts/prod"
}