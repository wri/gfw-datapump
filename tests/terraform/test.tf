resource "aws_s3_bucket" "pipelines_test" {
  bucket = "gfw-pipelines-test"
  acl    = "private"
  force_destroy = true
}

resource "aws_s3_bucket" "terraform_test" {
  bucket = "gfw-terraform-test"
  acl    = "private"
  force_destroy = true
}

resource "aws_s3_bucket_object" "shapely_pyyaml" {
  bucket = aws_s3_bucket.pipelines_test.id
  key    = "lambda_layers/shapely_pyyaml.zip"
  source = "../lambda_layers/shapely_pyyaml.zip"
  etag   = filemd5("../lambda_layers/shapely_pyyaml.zip")
}

resource "aws_lambda_layer_version" "shapely_pyyaml" {
  layer_name          = substr("$test-shapely_pyyaml", 0, 64)
  s3_bucket           = aws_s3_bucket_object.shapely_pyyaml.bucket
  s3_key              = aws_s3_bucket_object.shapely_pyyaml.key
  compatible_runtimes = ["python3.7"]
  source_code_hash    = filebase64sha256("../lambda_layers/shapely_pyyaml.zip")
}

resource "aws_s3_bucket_object" "rasterio" {
  bucket = aws_s3_bucket.pipelines_test.id
  key    = "lambda_layers/rasterio.zip"
  source = "../lambda_layers/rasterio.zip"
  etag   = filemd5("../lambda_layers/rasterio.zip")
}

resource "aws_lambda_layer_version" "rasterio" {
  layer_name          = substr("test-rasterio", 0, 64)
  s3_bucket           = aws_s3_bucket_object.rasterio.bucket
  s3_key              = aws_s3_bucket_object.rasterio.key
  compatible_runtimes = ["python3.7"]
  source_code_hash    = filebase64sha256("../lambda_layers/rasterio.zip")
}
