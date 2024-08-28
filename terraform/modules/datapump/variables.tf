variable "environment" {
  type        = string
  description = "An environment namespace for the infrastructure."
}

variable "data_api_uri" {
  type        = string
  description = "URI for data API."
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

variable "lambda_params" {
  type        = object({
    runtime     = string
    memory_size = number
    timeout     = number
  })
  description = "Lambda parameters"
  default = {
    runtime = "python3.10"
    memory_size = 3048
    timeout = 900
  }
}

variable "geotrellis_jar_path" {
  type        = string
  description = "Fat Jar to use to run Geotrellis Spark Job"
}

variable "emr_instance_profile_name" {
  default     = ""
  type        = string
  description = "EMR instance profile"
}

variable "emr_service_role_name" {
  default     = ""
  type        = string
  description = "EMR service role"
}

variable "ec2_key_name" {
  default     = ""
  type        = string
  description = "Key pair to use for SSHing into EC2"
}

variable "subnet_ids" {
  default     = []
  type        = list(string)
  description = "Subnet IDs to run on"
}

variable "pipelines_bucket" {
  type        = string
  description = "Pipelines bucket to store intermediate results"
}

variable "data_lake_bucket" {
  type        = string
  description = "Data lake bucket to store intermediate results"
}

variable "tags" {}

variable "sfn_wait_time" {
  type        = number
  description = "Time to wait in between steps of step function"
}

variable "numpy_lambda_layer_arn" {
  type        = string
  description = "ARN of the numpy lambda layer"
}

variable "rasterio_lambda_layer_arn" {
  type        = string
  description = "ARN of the rasterio lambda layer"
}

variable "shapely_lambda_layer_arn" {
  type        = string
  description = "ARN of the shapely lambda layer"
}

variable "glad_path" {
  type        = string
  description = "S3 path to GLAD data"
}

variable "command_runner_jar" {
  type        = string
  description = "Path to command-runner.jar for EMR"
  default = "command-runner.jar"
}

variable "gcs_secret_arn" {
  type        = string
  default     = ""
  description = "ARN to read GCS secret"
}

variable "read_gfw_api_secrets_policy" {
  type        = string
  default     = ""
  description = "ARN to policy to read gfw api secrets"
}

variable "read_gfw_sync_secrets_policy" {
  type        = string
  default     = ""
  description = "ARN to policy to read gfw sync secrets"
}