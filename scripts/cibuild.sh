#!/usr/bin/env bash

set -e

GIT_SHA="$(git rev-parse HEAD | cut -c 1-8)"

build_lambda_package() {
  IMAGE="gfw/${1}_lambda"

  echo "BUILD image ${IMAGE}"
  docker build --no-cache -t ${IMAGE}:${GIT_SHA} -f lambdas/${1}/Dockerfile .

  echo "CREATE container"
  docker run --name lambda -itd ${IMAGE}:${GIT_SHA} /bin/bash

  echo "RUN tests"
  docker exec -d lambda pytest

  echo "COPY ZIP package to host"
  docker cp lambda:/var/task/lambda.zip lambdas/${1}/lambda.zip

  echo "REMOVE container"
  docker rm -f lambda
}

lambdas=( check_datasets_saved check_new_areas submit_job update_new_area_statuses upload_results_to_datasets )

for l in ${lambdas[@]}
do
    echo "Build package for lambda ${l}"
    build_lambda_package ${l}
done