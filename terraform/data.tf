data "template_file" "sts_assume_role_lambda" {
  template = file("policies/sts_assume_role_lambda.json")
}

data "template_file" "sts_assume_role_states" {
  template = file("policies/sts_assume_role_states.json")
}

data "template_file" "geotrellis_summary_update" {
  template = file("policies/datapump.json")
}

data "template_file" "sfn_geotrellis_summary_update" {
  template = file("../step_functions/geotrellis_dataset.json")
  vars = {
    lambda_submit_job_arn     = aws_lambda_function.submit_job.arn,
    lambda_upload_results_arn = aws_lambda_function.upload_results_to_datasets.arn,
    lambda_check_dataset_arn  = aws_lambda_function.check_datasets_saved.arn
  }
}

data "template_file" "sfn_summarize_new_aoi" {
  template = file("../step_functions/new_user_aoi.json")
  vars = {
    lambda_check_new_aoi_arn         = aws_lambda_function.check_new_aoi.arn,
    lambda_update_new_aoi_status_arn = aws_lambda_function.update_new_aoi_statuses.arn,
    state_machine_arn                = aws_sfn_state_machine.geotrellis_dataset.id
  }
}

data "terraform_remote_state" "core" {
  backend = "s3"
  config = {
    bucket = local.tf_state_bucket
    region = "us-east-1"
    key    = "core.tfstate"
  }
}