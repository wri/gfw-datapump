output "sfn_datapump" {
  value = aws_sfn_state_machine.datapump.id
}

//output "sfn_datapump_arn" {
//  value = aws_sfn_state_machine.datapump.arn
//}

output "base_url" {
  value = aws_api_gateway_deployment.api_gw_dep.invoke_url
}

output "gateway_lambda_name" {
  value = aws_lambda_function.fastapi.function_name
}

output "rest_api_execution_arn" {
  value = aws_api_gateway_rest_api.api_gw_api.execution_arn
}