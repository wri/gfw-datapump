#!/usr/bin/env bash

pip install -e .
pip install -r requirements-dev.txt

detect-secrets scan > .secrets.baseline
pre-commit install
