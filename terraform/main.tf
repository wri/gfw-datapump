terraform {
  required_version = ">=0.12.13"
//  backend "s3" {
//    key     = "user-aoi-batch.tfstate"
//    region  = "us-east-1"
//    encrypt = true
//  }
}

# Download any stable version in AWS provider of 2.36.0 or higher in 2.36 train
//provider "aws" {
//  region  = "us-east-1"
//  version = "~> 2.36.0"
//}
provider "aws" {
  region = "us-east-1"
  skip_credentials_validation = true
  skip_requesting_account_id = true
  skip_metadata_api_check = true
  s3_force_path_style = true
  endpoints {
//    s3 = "https://localhost:4571" // "http://localhost:4572"
//    iam = "https://localhost:4567"
//    stepfunctions = "https://localhost:4570"
//    lambda = "https://localhost:4568"
//    cloudwatch = "https://localhost:4569"
    s3 = "http://localstack:4566" // "http://localhost:4572"
    iam = "http://localstack:4566"
    stepfunctions = "http://localstack:4566"
    lambda = "http://localstack:4566"
    cloudwatch = "http://localstack:4566"
  }
}

//module "lambda_layers" {
//  source      = "./modules/lambda_layers"
//  s3_bucket   = local.tf_state_bucket
//  project     = local.project
//  name_suffix = local.name_suffix
//}