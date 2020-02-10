
resource "aws_s3_bucket_object" "datapump_utils" {
  bucket = var.s3_bucket
  key    = "lambda_layers/datapump_utils.zip"
  source = "../docker/datapump_utils/layer.zip"
  etag   = filemd5("../docker/datapump_utils/layer.zip")
}

resource "aws_lambda_layer_version" "datapump_utils" {
  layer_name          = substr("${var.project}-datapump_utils${var.name_suffix}", 0, 64)
  s3_bucket           = aws_s3_bucket_object.datapump_utils.bucket
  s3_key              = aws_s3_bucket_object.datapump_utils.key
  compatible_runtimes = ["python3.7"]
  source_code_hash    = "${filebase64sha256("../docker/datapump_utils/layer.zip")}"
}

