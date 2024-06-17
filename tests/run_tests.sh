#!/bin/sh

set -e

# if ! [ -f "/app/tests/files/mock_geotrellis/target/geotrellis-mock-0.1.0-shaded.jar" ]; then
#  cd /app/tests/files/mock_geotrellis
#  mvn package
#  if [[ "$?" -ne 0 ]] ; then
#    echo 'Error building mock geotrellis jar, exiting'; exit 1
#  fi
# fi

# mkdir -p /app/tests/logs

# cd /app/tests/terraform
# terraform init && terraform plan -var-file="/app/tests/terraform/terraform-test.tfvars" && terraform apply -auto-approve -var-file="/app/tests/terraform/terraform-test.tfvars"

# cd /app/tests
# pytest tests
