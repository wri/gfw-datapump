data "archive_file" "lambda_dispatcher" {
  type        = "zip"
  source_dir  = "${var.lambdas_path}/dispatcher/src"
  output_path = "${var.lambdas_path}/dispatcher/lambda.zip"
}

data "archive_file" "lambda_executor" {
  type        = "zip"
  source_dir  = "${var.lambdas_path}/executor/src"
  output_path = "${var.lambdas_path}/executor/lambda.zip"
}

data "archive_file" "lambda_postprocessor" {
  type        = "zip"
  source_dir  = "${var.lambdas_path}/postprocessor/src"
  output_path = "${var.lambdas_path}/postprocessor/lambda.zip"
}
