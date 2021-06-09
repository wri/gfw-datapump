output "sfn_datapump" {
  value = aws_sfn_state_machine.datapump.id
}

output "base_url" {
  value = aws_api_gateway_deployment.example.invoke_url
}

output "gateway_lambda_name" {
  value = aws_lambda_function.gateway_lambda.function_name
}

output "rest_api_execution_arn" {
  value = aws_api_gateway_rest_api.example.execution_arn
}