#!/usr/bin/env bash

set -e

docker-compose build

pip install -e .
pip install -r requirements-dev.txt

detect-secrets scan > .secrets.baseline
pre-commit install
