import json
import os
import io
from typing import Set

from datapump_utils.exceptions import UnexpectedResponseError
from datapump_utils.util import error
from datapump_utils.secrets import token
from datapump_utils.summary_analysis import get_dataset_sources
from datapump_utils.logger import get_logger
from datapump_utils.slack import slack_webhook
import requests


if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"

LOGGER = get_logger(__name__)


def handler(event, context):
    try:
        if ENV == "production":
            uri_domain = "data-api.globalforestwatch.org"
        else:
            uri_domain = "staging-data-api.globalforestwatch.org"

        uri = f"https://{uri_domain}/dataset/nasa_viirs_fire_alerts/{os.environ['DATA_API_VIIRS_VERSION']}"

        if isinstance(event, list):
            for output in event:
                if "viirs_all" in output:
                    event = json.loads(
                        output["viirs_all"]["Output"]
                    )  # workaround because nested step functions serialize the output

                datasets = event["datasets"]
                viirs_all_ds = datasets["firealerts_viirs"]["all"]
                ds_result_path = event["dataset_result_paths"][viirs_all_ds[0]]
                ds_sources = get_dataset_sources(ds_result_path, raw_s3=True)

                headers = {
                    "Authorization": f"Bearer {token()}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "source_uri": ds_sources,
                }

                LOGGER.info(f"Calling PATCH on {uri} with payload:\n{payload}")
                resp = requests.post(f"{uri}/append", headers=headers, json=payload)

                if resp.status_code >= 300:
                    raise UnexpectedResponseError(
                        f"Got status code {resp.status_code} while posting to data API"
                    )

                return {"status": "PENDING"}
        else:
            resp = requests.get(f"{uri}/assets")
            if resp.status_code >= 300:
                raise UnexpectedResponseError(
                    f"Got status code {resp.status_code} while making call to data API"
                )

            status = resp.json()["data"][0]["status"]

            if status == "saved":
                slack_webhook("INFO", "Successfully injected VIIRS alerts to data API")
                return {"status": "SUCCESS"}
            elif status == "failed":
                return error("Failed to inject data to data API")
            elif status == "pending":
                return {"status": "PENDING"}
    except Exception as e:
        return error(f"Exception while injecting fire data to API: {str(e)}")
