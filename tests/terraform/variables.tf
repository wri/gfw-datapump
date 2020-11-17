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
  description = "Runtime version for AWS Lambda"
}

variable "step_functions_path" {
  type        = string
  description = "Runtime version for AWS Lambda"
}

variable "lambda_analyzer" {
  type        = object({
    runtime     = string
    memory_size = number
    timeout     = number
  })
  description = "Lambda parameters"
}

variable "lambda_uploader" {
  type        = object({
    runtime     = string
    memory_size = number
    timeout     = number
  })
  description = "Lambda parameters"
}

variable "lambda_dispatcher" {
  type        = object({
    runtime     = string
    memory_size = number
    timeout     = number
  })
  description = "Lambda parameters"
}

variable "geotrellis_jar" {
  type        = string
  description = "Fat Jar to use to run Geotrellis Spark Job"
}