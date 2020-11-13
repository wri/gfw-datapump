data "archive_file" "lambda_analyzer" {
  type        = "zip"
  source_dir  = "${var.lambdas_path}/analyzer/src"
  output_path = "${var.lambdas_path}/analyzer/lambda.zip"
}

data "archive_file" "lambda_uploader" {
  type        = "zip"
  source_dir  = "${var.lambdas_path}/uploader/src"
  output_path = "${var.lambdas_path}/uploader/lambda.zip"
}
