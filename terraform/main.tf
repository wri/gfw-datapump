terraform {
  required_version = ">=0.12.13"
  backend "s3" {
    key     = "user-aoi-batch.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}
