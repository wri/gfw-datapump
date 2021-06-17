environment = "dev"

step_functions_path = "../src/step_functions"
lambdas_path = "../src/lambdas"
policies_path = "../terraform/modules/datapump/policies"
lambda_layers_path = "../src"

//data_api_uri = "https://staging-data-api.globalforestwatch.org"
data_api_uri = "http://gfw-data-api-elb-16bpp-pngs-1496121072.us-east-1.elb.amazonaws.com"

geotrellis_jar_path = "s3://gfw-pipelines-dev/geotrellis/jars"