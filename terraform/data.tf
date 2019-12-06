data "template_file" "sts_assume_role_lambda" {
  template = file("policies/sts_assume_role_lambda.json")
}

data "template_file" "sts_assume_role_states" {
  template = file("policies/sts_assume_role_states.json")
}

data "template_file" "geotrellis_summary_update" {
  template = file("policies/geotrellis_summary_update.json")
}

data "template_file" "sfn_geotrellis_summary_update" {
  template = file("../step_functions/geotrellis_summary_update.json")
  vars = {
    lambda_submit_job_arn     = aws_lambda_function.submit_job.arn,
    lambda_upload_results_arn = aws_lambda_function.upload_results_to_datasets.arn,
    lambda_check_dataset_arn  = aws_lambda_function.check_datasets_saved.arn
  }
}

data "template_file" "sfn_summarize_new_areas" {
  template = file("../step_functions/summarize_new_areas.json")
  vars = {
    lambda_check_new_areas_arn        = aws_lambda_function.check_new_areas.arn,
    lambda_update_new_area_status_arn = aws_lambda_function.update_new_area_statuses.arn,
    state_machine_arn                 = aws_sfn_state_machine.geotrellis_summary_update.id
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