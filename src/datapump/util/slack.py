import json

import boto3
import requests

from ..globals import GLOBALS


def slack_webhook(level, message):
    if GLOBALS.env == "production":
        channel: str = "data-updates"
    elif GLOBALS.env == "staging":
        channel = "data-updates-staging"
    else:
        return
    app = "GFW SYNC - DATAPUMP - DATASET UPDATE"

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

    url = get_slack_webhook(channel)
    return requests.post(url, json=attachment)


def get_slack_webhook(channel):
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId="slack/gfw-sync")
    return json.loads(response["SecretString"])[channel]
