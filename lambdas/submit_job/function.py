from botocore.exceptions import ClientError
from summary_analysis_batch.utils import slack_webhook, s3_directory_exists
from summary_analysis_batch.summary_batch_job import get_summary_analysis_step, submit_summary_batch_job
import datetime

RESULT_BUCKET = "gfw-pipelines-dev"
RESULT_PREFIX = "geotrellis/results/{date_version}/{name}"
RESULT_PREFIX = "geotrellis/results/{date_version}/{name}"
RESULT_PATH = "s3://{}/{}"


#  s3://gfw-pipelines-dev/geotrellis/results/v20191119/new_area_test/gladalerts/gladAlerts_20191119_2106/geostore/daily_alerts/part-00000-41e4a658-6254-48ba-a35c-46ea3297cc50-c000.csv

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
        for analysis in analyses:
            result_url = RESULT_PATH.format(RESULT_BUCKET, result_dir)
            steps.append(get_summary_analysis_step(analysis["name"], feature_src, result_url, feature_type))

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
            "result_dir": result_dir
        }
    except ClientError:
        slack_webhook("ERROR", "Error submitting job to update {} summary datasets.".format(name))
        return {"status": "FAILED"}


if __name__ == "__main__":
    print(handler({
        "env": "dev",
        "name": "new_area_test",
        "feature_src": "s3://gfw-pipelines-dev/geotrellis/features/*.tsv",
        "feature_type": "geostore",
        "analyses": [{
            "name": "gladalerts",
            "sub_analyses": [{
                "name": "daily_alerts",
                "dataset": "sdfgdsg"

            }]
        }]
    }, None))