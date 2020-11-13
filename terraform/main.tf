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