terraform {
  required_version = ">= 0.13, < 0.14"
  backend "s3" {
    key     = "user-aoi-batch.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
  required_providers {
    aws = {
      source   = "hashicorp/aws"
      version  = ">= 4, < 5"
    }
  }
}

provider "aws" {
  version  = ">= 4, < 5"
  region  = "us-east-1"
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
  sfn_wait_time = 120
  data_api_uri = var.data_api_uri
  data_lake_bucket = data.terraform_remote_state.core.outputs.data-lake_bucket
  numpy_lambda_layer_arn = data.terraform_remote_state.lambda-layers.outputs.py310_numpy_arn
  rasterio_lambda_layer_arn = data.terraform_remote_state.lambda-layers.outputs.py310_rasterio_no_numpy_arn
  shapely_lambda_layer_arn = data.terraform_remote_state.lambda-layers.outputs.py310_shapely_no_numpy_arn
  glad_path = local.glad_path
  emr_instance_profile_name = data.terraform_remote_state.core.outputs.emr_instance_profile_name
  emr_service_role_name = data.terraform_remote_state.core.outputs.emr_service_role_name
  subnet_ids = data.terraform_remote_state.core.outputs.private_subnet_ids
  ec2_key_name = data.terraform_remote_state.core.outputs.key_pair_jterry_gfw
  gcs_secret_arn = data.terraform_remote_state.core.outputs.secrets_read-gfw-gee-export_arn
  read_gfw_api_secrets_policy = data.terraform_remote_state.core.outputs.secrets_read-gfw-api-token_policy_arn
  read_gfw_sync_secrets_policy = data.terraform_remote_state.core.outputs.secrets_read-slack-gfw-sync_policy_arn
}

locals {
  bucket_suffix               = var.environment == "production" ? "" : "-${var.environment}"
  tf_state_bucket             = "gfw-terraform${local.bucket_suffix}"
  tags                        = merge({
      Job = "Data Pump",
  }, data.terraform_remote_state.core.outputs.tags)
  name_suffix                 = "-${terraform.workspace}"
  project                     = "datapump"
  glad_path                   = "s3://gfw2-data/forest_change/umd_landsat_alerts/prod"
}