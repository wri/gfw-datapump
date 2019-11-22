from botocore.exceptions import ClientError
from summary_analysis_batch.utils import slack_webhook, s3_directory_exists
from summary_analysis_batch.summary_batch_job import get_summary_analysis_step, submit_summary_batch_job
import boto3
import datetime


def handler(event, context):
    env = event["env"]

    try:
        s3_client = boto3.client("s3")
        if s3_directory_exists(NEW_AOI_BUCKET, NEW_AOI_PREFIX, s3_client):
            aoi_url = "s3://{}/{}/*.tsv".format(NEW_AOI_BUCKET, NEW_AOI_PREFIX)
            return {
                "status": "FOUND_NEW"
            }.update(event)
    except ClientError:
        slack_webhook("INFO", "No new user areas found. Doing nothing.")
        return {"status": "NOTHING_TO_DO"}