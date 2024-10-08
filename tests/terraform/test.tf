resource "aws_s3_bucket" "pipelines_test" {
  bucket = "gfw-pipelines-test"
  acl    = "private"
  force_destroy = true
}

resource "aws_s3_bucket" "data_lake_test" {
  bucket = "gfw-data-lake-test"
  acl    = "private"
  force_destroy = true
}


resource "aws_s3_bucket" "terraform_test" {
  bucket = "gfw-terraform-test"
  acl    = "private"
  force_destroy = true
}

resource "aws_s3_bucket_object" "qc_1x1" {
  bucket = aws_s3_bucket.pipelines_test.id
  key    = "test_zonal_stats/vtest1/vector/epsg-4326/test_zonal_stats_vtest1_1x1.tsv"
  source = "../files/qc.tsv"
  etag   = filemd5("../files/qc.tsv")
}


resource "aws_s3_bucket_object" "geotrellis_results" {
  for_each = fileset("../files/geotrellis_results", "**/*.csv")

  bucket = aws_s3_bucket.pipelines_test.id
  key    = "geotrellis/results/vteststats1/test_zonal_stats/${each.value}"
  source = "../files/geotrellis_results/${each.value}"
}

resource "aws_s3_bucket_object" "geotrellis_results_sync_glad" {
  for_each = fileset("../files/geotrellis_results/gladalerts", "**/{daily,weekly}_alerts/*.csv")

  bucket = aws_s3_bucket.pipelines_test.id
  key    = "geotrellis/results/v20210122/test_zonal_stats/glad/gladalerts/${each.value}"
  source = "../files/geotrellis_results/gladalerts/${each.value}"
}

resource "aws_s3_bucket_object" "geotrellis_results_sync_integrated_alerts" {
  for_each = fileset("../files/geotrellis_results/integrated_alerts", "**/{daily,weekly}_alerts/*.csv")

  bucket = aws_s3_bucket.pipelines_test.id
  key    = "geotrellis/results/v20210122/test_zonal_stats/integrated_alerts/integrated_alerts/${each.value}"
  source = "../files/geotrellis_results/integrated_alerts/${each.value}"
}

resource "aws_s3_bucket_object" "geotrellis_jar" {
  bucket = aws_s3_bucket.pipelines_test.id
  key    = "geotrellis-mock.jar"
  source = "../files/mock_geotrellis/target/geotrellis-mock-0.1.0-shaded.jar"
  etag   = filemd5("../files/mock_geotrellis/target/geotrellis-mock-0.1.0-shaded.jar")
}


resource "aws_s3_bucket_object" "glad_status" {
  bucket = aws_s3_bucket.pipelines_test.id
  key    = "glad/events/status"
  source = "../files/status"
  etag   = filemd5("../files/status")
}

resource "aws_s3_bucket_object" "numpy" {
  bucket = aws_s3_bucket.pipelines_test.id
  key    = "lambda_layers/numpy.zip"
  source = "../files/numpy.zip"
  etag   = filemd5("../files/numpy.zip")
}

resource "aws_s3_bucket_object" "rasterio" {
  bucket = aws_s3_bucket.pipelines_test.id
  key    = "lambda_layers/rasterio.zip"
  source = "../files/rasterio.zip"
  etag   = filemd5("../files/rasterio.zip")
}

resource "aws_s3_bucket_object" "shapely" {
  bucket = aws_s3_bucket.pipelines_test.id
  key    = "lambda_layers/shapely.zip"
  source = "../files/shapely.zip"
  etag   = filemd5("../files/shapely.zip")
}

resource "aws_lambda_layer_version" "numpy" {
  layer_name          = substr("test-numpy", 0, 64)
  s3_bucket           = aws_s3_bucket_object.numpy.bucket
  s3_key              = aws_s3_bucket_object.numpy.key
  compatible_runtimes = ["python3.10"]
  source_code_hash    = filebase64sha256("../files/numpy.zip")
}

resource "aws_lambda_layer_version" "rasterio" {
  layer_name          = substr("test-rasterio", 0, 64)
  s3_bucket           = aws_s3_bucket_object.rasterio.bucket
  s3_key              = aws_s3_bucket_object.rasterio.key
  compatible_runtimes = ["python3.10"]
  source_code_hash    = filebase64sha256("../files/rasterio.zip")
}

resource "aws_lambda_layer_version" "shapely" {
  layer_name          = substr("test-shapely", 0, 64)
  s3_bucket           = aws_s3_bucket_object.shapely.bucket
  s3_key              = aws_s3_bucket_object.shapely.key
  compatible_runtimes = ["python3.10"]
  source_code_hash    = filebase64sha256("../files/shapely.zip")
}

module "api_token_secret" {
  source        = "git::https://github.com/wri/gfw-terraform-modules.git//terraform/modules/secrets?ref=master"
  project       = "test_proj"
  name          = "gfw-api/token"
  secret_string = jsonencode({ "token" = "test_token", "email" = "gfw-sync@test.org" })
}

module "slack_secret" {
  source        = "git::https://github.com/wri/gfw-terraform-modules.git//terraform/modules/secrets?ref=master"
  project       = "test_proj"
  name          = "slack/gfw-sync"
  secret_string = jsonencode({ "data-updates" = "test_hook" })
}