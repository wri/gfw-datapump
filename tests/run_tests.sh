#!/bin/sh

set -e

if ! [ -f "/app/tests/files/mock_geotrellis/target/geotrellis-mock-0.1.0-shaded.jar" ]; then
  cd /app/tests/files/mock_geotrellis
  mvn package
fi

cd /app/tests/terraform
terraform init && terraform plan -var-file="/app/tests/terraform/terraform-test.tfvars" && terraform apply -auto-approve -var-file="/app/tests/terraform/terraform-test.tfvars"
cd /app/tests

pytest tests