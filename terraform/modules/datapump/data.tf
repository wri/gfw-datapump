data "template_file" "sts_assume_role_lambda" {
  template = file("${var.policies_path}/sts_assume_role_lambda.json")
}

data "template_file" "sts_assume_role_states" {
  template = file("${var.policies_path}/sts_assume_role_states.json")
}

data "template_file" "datapump_policy" {
  template = file("${var.policies_path}/datapump.json.tmpl"),
  vars = {
    gcs_secret_arn = var.gcs_secret_arn
  }
}

data "template_file" "sfn_datapump" {
  template = file("${var.step_functions_path}/datapump.json.tmpl")
  vars = {
    lambda_dispatcher_arn = aws_lambda_function.dispatcher.arn,
    lambda_executor_arn = aws_lambda_function.executor.arn,
    lambda_postprocessor_arn = aws_lambda_function.postprocessor.arn,
    wait_time = var.sfn_wait_time
  }
}

module "py37_datapump_020" {
  source         = "git::https://github.com/wri/gfw-lambda-layers.git//terraform/modules/lambda_layer"
  bucket         = var.pipelines_bucket
  name           = "datapump-${terraform.workspace}"
  module_version = "0.2.0"
  runtime        = "python3.7"
  layer_path     = "${var.lambda_layers_path}/"
}