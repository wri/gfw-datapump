locals {
  lambda_submit_job_file               = "../lambdas/submit_job/lambda.zip"
  lambda_upload_results_file           = "../lambdas/upload_results_to_datasets/lambda.zip"
  lambda_check_dataset_file            = "../lambdas/check_datasets_saved/lambda.zip"
  lambda_check_new_area_file           = "../lambdas/check_new_areas/lambda.zip"
  lambda_update_new_area_statuses_file = "../lambdas/update_new_area_statuses/lambda.zip"
  bucket_suffix                        = var.environment == "production" ? "" : "-${var.environment}"
  tf_state_bucket                      = "gfw-terraform${local.bucket_suffix}"
  tags                                 = data.terraform_remote_state.core.outputs.tags
}