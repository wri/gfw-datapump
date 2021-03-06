import logging
import os
import traceback

from botocore.exceptions import ClientError

from datapump_utils.summary_analysis import (
    get_summary_analysis_steps,
    submit_summary_batch_job,
)
from datapump_utils.util import get_date_string, bucket_suffix
from datapump_utils.slack import slack_webhook
from datapump_utils.util import error


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
    instance_count = event["instance_count"]
    get_summary = event.get("get_summary", False)
    fire_config = event.get("fire_config", None)
    geotrellis_jar = event.get("geotrellis_jar", None)

    result_dir = f"geotrellis/results/{name}/{get_date_string()}"

    try:
        steps = get_summary_analysis_steps(
            analyses,
            feature_src,
            feature_type,
            result_dir,
            get_summary,
            fire_config,
            geotrellis_jar,
        )
        job_flow_id = submit_summary_batch_job(name, steps, instance_count)

        event.update(
            {"status": "SUCCESS", "job_flow_id": job_flow_id, "result_dir": result_dir}
        )

        return event
    except Exception as e:
        return error(f"Exception caught while running {name} update: {e}")
