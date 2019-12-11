output "datapump_utils_arn" {
  value       = aws_lambda_layer_version.datapump_utils.layer_arn
  description = "ARN of datapump_utils lambda layer"
}