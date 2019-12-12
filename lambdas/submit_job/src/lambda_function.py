import logging
import os
import traceback

from botocore.exceptions import ClientError

from datapump_utils.summary_analysis import (
    get_summary_analysis_steps,
    submit_summary_batch_job,
)
from datapump_utils.util import get_curr_date_dir_name, bucket_suffix
from datapump_utils.slack import slack_webhook


# environment should be set via environment variable. This can be done when deploying the lambda function.
if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"


def handler(event, context):
    name = event["name"]
    feature_src = event["feature_src"]
    feature_type = event["feature_type"]
    analyses = event["analyses"]
    instance_size = event["instance_size"]
    instance_count = event["instance_count"]
    get_summary = event["get_summary"]

    result_dir = f"geotrellis/results/{name}/{get_curr_date_dir_name()}"

    try:
        steps = get_summary_analysis_steps(
            analyses, feature_src, feature_type, result_dir, get_summary
        )
        job_flow_id = submit_summary_batch_job(
            name, steps, instance_size, instance_count
        )

        event.update(
            {"status": "SUCCESS", "job_flow_id": job_flow_id, "result_dir": result_dir}
        )

        return event
    except ClientError:
        logging.error(traceback.print_exc())
        slack_webhook(
            "ERROR", f"Error submitting job to update {ENV} summary datasets.",
        )
        return {"status": "FAILED"}
