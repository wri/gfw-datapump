variable "environment" {
  type        = string
  description = "An environment namespace for the infrastructure."
}

variable "policies_path" {
  type        = string
  description = "Runtime version for AWS Lambda"
}

variable "lambdas_path" {
  type        = string
  description = "Runtime version for AWS Lambda"
}

variable "lambda_layers_path" {
  type        = string
  description = "Runtime version for AWS Lambda"
}

variable "step_functions_path" {
  type        = string
  description = "Runtime version for AWS Lambda"
}

variable "lambda_analyzer_runtime" {
  type        = string
  description = "Runtime version for AWS Lambda"
}

variable "lambda_uploader_runtime" {
  type        = string
  description = "Runtime version for AWS Lambda"
}

variable "lambda_analyzer_memory_size" {
  type        = number
  description = "Memory limit in MB for AWS Lambda function"
}

variable "lambda_uploader_memory_size" {
  type        = number
  description = "Memory limit in MB for AWS Lambda function"
}

variable "lambda_analyzer_timeout" {
  type        = number
  description = "Timeout in sec for AWS Lambda function"
}

variable "lambda_uploader_timeout" {
  type        = number
  description = "Timeout in sec for AWS Lambda function"
}

variable "geotrellis_jar" {
  type        = string
  description = "Fat Jar to use to run Geotrellis Spark Job"
}