variable "environment" {
  type        = string
  description = "An environment namespace for the infrastructure."
}

variable "lambda_submit_job_runtime" {
  type        = string
  description = "Runtime version for AWS Lambda"
}

variable "lambda_upload_results_runtime" {
  type        = string
  description = "Runtime version for AWS Lambda"
}

variable "lambda_check_datasets_runtime" {
  type        = string
  description = "Runtime version for AWS Lambda"
}

variable "lambda_check_new_aoi_runtime" {
  type        = string
  description = "Runtime version for AWS Lambda"
}

variable "lambda_check_new_glad_alerts_runtime" {
  type        = string
  description = "Runtime version for AWS Lambda"
}

variable "lambda_update_new_aoi_statuses_runtime" {
  type        = string
  description = "Runtime version for AWS Lambda"
}

variable "lambda_submit_job_memory_size" {
  type        = number
  description = "Memory limit in MB for AWS Lambda function"
}

variable "lambda_upload_results_memory_size" {
  type        = number
  description = "Memory limit in MB for AWS Lambda function"
}

variable "lambda_check_datasets_memory_size" {
  type        = number
  description = "Memory limit in MB for AWS Lambda function"
}

variable "lambda_check_new_aoi_memory_size" {
  type        = number
  description = "Memory limit in MB for AWS Lambda function"
}

variable "lambda_check_new_glad_alerts_memory_size" {
  type        = number
  description = "Memory limit in MB for AWS Lambda function"
}

variable "lambda_update_new_aoi_statuses_memory_size" {
  type        = number
  description = "Memory limit in MB for AWS Lambda function"
}

variable "lambda_submit_job_timeout" {
  type        = number
  description = "Timeout in sec for AWS Lambda function"
}

variable "lambda_upload_results_timeout" {
  type        = number
  description = "Timeout in sec for AWS Lambda function"
}

variable "lambda_check_datasets_timeout" {
  type        = number
  description = "Timeout in sec for AWS Lambda function"
}

variable "lambda_check_new_aoi_timeout" {
  type        = number
  description = "Timeout in sec for AWS Lambda function"
}

variable "lambda_check_new_glad_alerts_timeout" {
  type        = number
  description = "Timeout in sec for AWS Lambda function"
}

variable "lambda_update_new_aoi_statuses_timeout" {
  type        = number
  description = "Timeout in sec for AWS Lambda function"
}

variable "geotrellis_jar" {
  type        = string
  description = "Fat Jar to use to run Geotrellis Spark Job"
}

variable "datasets" {
  description = "Dataset IDs in Resource Watch API for storing results of different analyses."
}