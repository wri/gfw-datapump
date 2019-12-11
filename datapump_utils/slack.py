import json
import os
import requests

import boto3

# environment should be set via environment variable. This can be done when deploying the lambda function.
if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"


def slack_webhook(level, message):
    if ENV == "production":
        app = "GFW SYNC - USER AOI BATCH"

        if level.upper() == "WARNING":
            color = "#E2AC37"
        elif level.upper() == "ERROR" or level.upper() == "CRITICAL":
            color = "#FF0000"
        else:
            color = "#36A64F"

        attachment = {
            "attachments": [
                {
                    "fallback": "{} - {} - {}".format(app, level.upper(), message),
                    "color": color,
                    "title": app,
                    "fields": [
                        {"title": level.upper(), "value": message, "short": False}
                    ],
                }
            ]
        }

        url = get_slack_webhook("data-updates")
        return requests.post(url, json=attachment)


def get_slack_webhook(channel):
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId="slack/gfw-sync")
    return json.loads(response["SecretString"])[channel]
