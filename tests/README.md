Tests are performed through extensive mocking using localstack and MockServer. Both are set up as local services using docker compose.

###Terraform
The mock environment is created by using mostly the same terraform code used for production deployment. This also allows testing of the infrastructure code.

In order to integrate with localstack, terraform is initiated from the tests/terraform folder, where a separate main.tf defines an AWS provider using the mocked local service as the endpoint.

Likewise, some of the terraform code relies on external terraform state. To mock this, test.tf includes any external infrastructure needed for testing.

###MockServer

MockServer is used to mock the gfw-data-api. The mock responses are defined through config file under files/mock_server. MockServer will just wait for expected API calls, and then return pre-configured responses. See MockServer documentation for more information.

###Geotrellis

Localstack allows you to mock EMR, and goes so far as to run a jar in a docker container with hadoop/spark installed. Running the actual geotrellis jar would be too slow though, so there's a mock jar under files/mock_geotrellis that just validates parameters. This is automatically built before running tests (maven must be installed).

Mock results are stored under files/geotrellis_results. Anything on that folder will be mapped to s3://gfw-pipeline-tests/geotrellis/results on localstack s3.

###Debugging

Because the tests are actually running in a fully mocked AWS, output and logs can be difficult to see through pytest console alone. However, logs for each service are written by localstack to the mocked CloudWatch. So after tests finish running, logs will be dumped from the mocked CloudWatch to the logs folder. For more debugging, the docker compose service logs are also dumped to that folder.

