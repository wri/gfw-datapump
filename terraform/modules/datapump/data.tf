data "template_file" "sts_assume_role_lambda" {
  template = file("${var.policies_path}/sts_assume_role_lambda.json")
}

data "template_file" "sts_assume_role_states" {
  template = file("${var.policies_path}/sts_assume_role_states.json")
}

data "template_file" "datapump_policy" {
  template = file("${var.policies_path}/datapump.json")
}

data "template_file" "sfn_datapump" {
  template = file("${var.step_functions_path}/datapump.json.tmpl")
  vars = {
    lambda_dispatcher_arn = aws_lambda_function.dispatcher.arn,
    lambda_analyzer_arn = aws_lambda_function.analyzer.arn,
    lambda_uploader_arn = aws_lambda_function.uploader.arn,
    lambda_postprocessor_arn = aws_lambda_function.postprocessor.arn,
    wait_time = var.sfn_wait_time
  }
}

module "lambda_layers" {
  source      = "../lambda_layers"
  s3_bucket   = var.pipelines_bucket
  project     = local.project
  name_suffix = local.name_suffix
  lambda_layers_path = var.lambda_layers_path
}

locals {
  config_db_s3_path = "s3://${var.pipelines_bucket}/datapump/config.db"
}