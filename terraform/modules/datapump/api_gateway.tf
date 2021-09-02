resource "aws_api_gateway_rest_api" "api_gw_api" {
  name = "APIGatewayDatapumpRestAPI"
  description = "Simple API to trigger datapump functionality"
}

resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.api_gw_api.id
  parent_id = aws_api_gateway_rest_api.api_gw_api.root_resource_id
  path_part = "{proxy+}"
}

resource "aws_api_gateway_method" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.api_gw_api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = "ANY"
  authorization = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "lambda" {
  rest_api_id = aws_api_gateway_rest_api.api_gw_api.id
  resource_id = aws_api_gateway_method.proxy.resource_id
  http_method = aws_api_gateway_method.proxy.http_method

  integration_http_method = "POST"
  type = "AWS_PROXY"
  uri = aws_lambda_function.fastapi.invoke_arn
}

// This is to match an empty path at the root of the API:
resource "aws_api_gateway_method" "proxy_root" {
  rest_api_id = aws_api_gateway_rest_api.api_gw_api.id
  resource_id = aws_api_gateway_rest_api.api_gw_api.root_resource_id
  http_method = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_root" {
  rest_api_id = aws_api_gateway_rest_api.api_gw_api.id
  resource_id = aws_api_gateway_method.proxy_root.resource_id
  http_method = aws_api_gateway_method.proxy_root.http_method

  integration_http_method = "POST"
  type = "AWS_PROXY"
  uri = aws_lambda_function.fastapi.invoke_arn
}

resource "aws_api_gateway_api_key" "umd_api_key" {
  name = "umd"
}

resource "aws_api_gateway_api_key" "wur_api_key" {
  name = "wur"
}

resource "aws_api_gateway_usage_plan" "example" {
  name         = "my-usage-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.api_gw_api.id
    stage  = aws_api_gateway_stage.testing.stage_name
  }

  quota_settings {
    limit  = 100
    period = "DAY"
  }

  throttle_settings {
    burst_limit = 5
    rate_limit  = 10
  }
}

resource "aws_api_gateway_usage_plan_key" "umd" {
  key_id        = aws_api_gateway_api_key.umd_api_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.example.id
}

resource "aws_api_gateway_usage_plan_key" "wur" {
  key_id        = aws_api_gateway_api_key.wur_api_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.example.id
}

resource "aws_api_gateway_deployment" "api_gw_dep" {
  depends_on = [
    aws_api_gateway_integration.lambda,
    aws_api_gateway_integration.lambda_root
  ]
  lifecycle {
    create_before_destroy = true
  }
  rest_api_id = aws_api_gateway_rest_api.api_gw_api.id
}

resource "aws_api_gateway_stage" "testing" {
  deployment_id = aws_api_gateway_deployment.api_gw_dep.id
  rest_api_id   = aws_api_gateway_rest_api.api_gw_api.id
  stage_name    = "testing"
}