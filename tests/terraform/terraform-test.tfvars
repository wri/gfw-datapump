environment = "test"

step_functions_path = "../../step_functions"
lambdas_path = "../../lambdas"
policies_path = "../../terraform/modules/datapump/policies"
lambda_layers_path = "../../docker"

lambda_analyzer_runtime     = "python3.7"
lambda_analyzer_memory_size = 1024
lambda_analyzer_timeout     = 300

lambda_uploader_runtime     = "python3.7"
lambda_uploader_memory_size = 1024
lambda_uploader_timeout     = 300

geotrellis_jar = "s3://gfw-pipelines-staging/geotrellis/jars/treecoverloss-assembly-1.1.2.jar"