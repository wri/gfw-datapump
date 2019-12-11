output "datapump_utils_arn" {
  value       = aws_lambda_layer_version.datapump_utils.arn
  description = "ARN of datapump_utils lambda layer"
}