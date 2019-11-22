from botocore.exceptions import ClientError
from geotrellis_summary_update.slack import slack_webhook
from geotrellis_summary_update.emr import get_summary_analysis_step, submit_summary_batch_job
import datetime
import logging
import traceback

RESULT_BUCKET = "gfw-pipelines-dev"
RESULT_PREFIX = "geotrellis/results/{date_version}/{name}"
RESULT_PREFIX = "geotrellis/results/{date_version}/{name}"
RESULT_PATH = "s3://{}/{}"


def handler(event, context):
    env = event["env"]
    name = event["name"]
    feature_src = event["feature_src"]
    feature_type = event["feature_type"]
    analyses = event["analyses"]

    today = datetime.datetime.today()
    date_version = "v{}{}{}".format(today.year, today.month, today.day)

    result_dir = RESULT_PREFIX.format(date_version=date_version, name=name)

    try:
        steps = []
        for analysis in analyses.keys():
            result_url = RESULT_PATH.format(RESULT_BUCKET, result_dir)
            steps.append(get_summary_analysis_step(analysis, feature_src, result_url, feature_type))

        job_flow_id = submit_summary_batch_job(name, steps, "r4.xlarge", 1, env)

        return {
            "status": "SUCCESS",
            "job_flow_id": job_flow_id,
            "env": env,
            "name": name,
            "analyses": analyses,
            "feature_src": feature_src,
            "feature_type": feature_type,
            "result_bucket": RESULT_BUCKET,
            "result_dir": result_dir,
            "upload_type": event["upload_type"]
        }
    except ClientError:
        logging.error(traceback.print_exc())
        slack_webhook("ERROR", "Error submitting job to update {} summary datasets.".format(name), env)
        return {"status": "FAILED"}


if __name__ == "__main__":
    print(handler({
        "env": "dev",
        "name": "new_area_test2",
        "feature_src": "s3://gfw-pipelines-dev/geotrellis/features/*.tsv",
        "feature_type": "geostore",
        "upload_type": "data-overwrite",
        "analyses": {
            "gladalerts": {
                "daily_alerts": "72af8802-df3c-42ab-a369-5e7f2b34ae2f",
                #"weekly_alerts": "Glad Alerts - Weekly - Geostore - User Areas",
                #"summary": "Glad Alerts - Summary - Geostore - User Areas",
            }
        }
    }, None))