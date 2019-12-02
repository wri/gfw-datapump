import logging
import os
import traceback

from botocore.exceptions import ClientError

from geotrellis_summary_update.emr import (
    get_summary_analysis_step,
    submit_summary_batch_job,
)
from geotrellis_summary_update.util import get_curr_date_dir_name, bucket_suffix
from geotrellis_summary_update.slack import slack_webhook


RESULT_BUCKET = f"gfw-pipelines-{bucket_suffix()}"
RESULT_PREFIX = "geotrellis/results/{name}/{date}"
RESULT_PATH = "s3://{}/{}"

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

    result_dir = RESULT_PREFIX.format(date=get_curr_date_dir_name(), name=name)

    try:
        steps = []
        for analysis in analyses.keys():
            result_url = RESULT_PATH.format(RESULT_BUCKET, result_dir)
            steps.append(
                get_summary_analysis_step(
                    analysis, feature_src, result_url, feature_type
                )
            )
            steps.append(
                get_summary_analysis_step(
                    analysis, feature_src, result_url, feature_type
                )
            )

        job_flow_id = submit_summary_batch_job(name, steps, "r4.xlarge", 1)

        return {
            "status": "SUCCESS",
            "job_flow_id": job_flow_id,
            "name": name,
            "analyses": analyses,
            "feature_src": feature_src,
            "feature_type": feature_type,
            "result_bucket": RESULT_BUCKET,
            "result_dir": result_dir,
            "upload_type": event["upload_type"],
        }
    except ClientError:
        logging.error(traceback.print_exc())
        slack_webhook(
            "ERROR", "Error submitting job to update {} summary datasets.".format(name)
        )
        return {"status": "FAILED"}
