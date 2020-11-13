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
  description = "Path to lambda layers"
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

variable "emr_instance_profile_name" {
  default     = null
  type        = string
  description = "EMR instance profile"
}

variable "emr_service_role_name" {
  default     = null
  type        = string
  description = "EMR service role"
}

variable "ec2_key_name" {
  default     = null
  type        = string
  description = "Key pair to use for SSHing into EC2"
}

variable "public_subnet_ids" {
  default     = null
  type        = list(string)
  description = "Public subnet IDs to run on"
}

variable "pipelines_bucket" {
  type        = string
  description = "Pipelines bucket to store intermediate results"
}

variable "tags" {}