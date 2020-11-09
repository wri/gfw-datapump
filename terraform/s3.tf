//resource "aws_s3_bucket_object" "extent_1x1" {
//  bucket = var.environment == "test" ? "test_bucket" : data.terraform_remote_state.core.outputs.pipelines_bucket
//  key    = "geotrellis/features/extent_1x1.geojson"
//  source = "../files/extent_1x1.geojson"
//  etag   = filemd5("../files/extent_1x1.geojson")
//}

resource "aws_s3_bucket" "gfw_terraform_dev" {
  bucket = "gfw-terraform-dev"
  acl    = "private"

  tags = {
    Name        = "My bucket"
    Environment = "Dev"
  }
}