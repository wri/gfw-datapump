terraform {
  required_version = ">=0.12.13"
  backend "s3" {
    key     = "user-aoi-batch.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}

# Download any stable version in AWS provider of 2.36.0 or higher in 2.36 train
provider "aws" {
  region  = "us-east-1"
  version = "~> 2.36.0"
}
