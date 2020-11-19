resource "aws_s3_bucket_object" "datapump" {
  bucket = var.s3_bucket
  key    = "lambda_layers/datapump.zip"
  source = "${var.lambda_layers_path}/datapump/layer.zip"
  etag   = filemd5("${var.lambda_layers_path}/datapump/layer.zip")
}

resource "aws_lambda_layer_version" "datapump" {
  layer_name          = substr("${var.project}-datapump${var.name_suffix}", 0, 64)
  s3_bucket           = aws_s3_bucket_object.datapump.bucket
  s3_key              = aws_s3_bucket_object.datapump.key
  compatible_runtimes = ["python3.7"]
  source_code_hash    = filebase64sha256("${var.lambda_layers_path}/datapump/layer.zip")
}

