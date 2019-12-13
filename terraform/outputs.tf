output "sfn_geotrellis_summary_update" {
  value = aws_sfn_state_machine.geotrellis_dataset.id
}

output "sfn_summarize_new_aoi" {
  value = aws_sfn_state_machine.new_user_aoi.id
}

output "sfn_summarize_new_glad_alerts" {
  value = aws_sfn_state_machine.new_glad_alerts.id
}

output "lambda_check_new_dataset_daved" {
  value = aws_lambda_function.check_datasets_saved.id
}

output "lambda_check_new_aoi" {
  value = aws_lambda_function.check_new_aoi.id
}

output "lambda_submit_job" {
  value = aws_lambda_function.submit_job.id
}

output "lambda_update_new_aoi_statuses" {
  value = aws_lambda_function.update_new_aoi_statuses.id
}

output "lambda_upload_results_to_datasets" {
  value = aws_lambda_function.upload_results_to_datasets.id
}

output "cloud_watch_event_rule_everyday-11-pm-est" {
  value = aws_cloudwatch_event_rule.everyday-11-pm-est.id
}
