environment = "test"

step_functions_path = "../src/step_functions"
lambdas_path = "../src/lambdas"
policies_path = "../terraform/modules/datapump/policies"
lambda_layers_path = "../src/docker"

data_api_uri = "https://staging-data-api.globalforestwatch.org"

lambda_analyzer = {
  runtime          = "python3.7"
  memory_size      = 3048
  timeout = 300
}

lambda_uploader = {
  runtime          = "python3.7"
  memory_size      = 3048
  timeout = 300
}

lambda_dispatcher = {
  runtime          = "python3.7"
  memory_size      = 3048
  timeout = 300
}

lambda_postprocessor = {
  runtime          = "python3.7"
  memory_size      = 3048
  timeout = 300
}

geotrellis_jar_path = "s3://gfw-pipelines-test/geotrellis/jars"