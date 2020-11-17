environment = "test"

step_functions_path = "../../step_functions"
lambdas_path = "../../lambdas"
policies_path = "../../terraform/modules/datapump/policies"
lambda_layers_path = "../../docker"

data_api_uri = "http://mock_server:1080"

lambda_analyzer = {
  runtime          = "python3.7"
  memory_size      = 1024
  timeout = 300
}

lambda_uploader = {
  runtime          = "python3.7"
  memory_size      = 1024
  timeout = 300
}

lambda_dispatcher = {
  runtime          = "python3.7"
  memory_size      = 1024
  timeout = 300
}

geotrellis_jar = "s3://gfw-pipelines-staging/geotrellis/jars/treecoverloss-assembly-1.1.2.jar"