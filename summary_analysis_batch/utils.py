from urllib.parse import urlparse
import requests
import boto3
import json


def s3_directory_exists(bucket, prefix, s3_client):
    return s3_client.list_objects(Bucket=bucket, Prefix=prefix)


def get_s3_path_parts(path):
    parsed = urlparse(path)
    bucket = parsed.netloc
    key = parsed.path
    return bucket, key


def slack_webhook(level, message, env="production"):
    if env != "dev" and env != "staging":
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