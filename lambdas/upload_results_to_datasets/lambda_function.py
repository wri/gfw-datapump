import os

import boto3
from botocore.exceptions import ClientError

from geotrellis_summary_update.slack import slack_webhook
from geotrellis_summary_update.dataset import upload_dataset
from geotrellis_summary_update.emr import RESULT_BUCKET

from enum import Enum

if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"

S3_CLIENT = boto3.client("s3")


def handler(event, context):
    job_flow_id = event["job_flow_id"]
    analyses = event["analyses"]
    result_dir = event["result_dir"]
    feature_type = event["feature_type"]
    name = event["name"]
    upload_type = event["upload_type"]

    # checks status of job
    emr_client = boto3.client("emr")

    error_message = "Failed to update {} summary datasets. Cluster with ID={} failed to complete analysis.".format(
        name, job_flow_id
    )

    job_status = get_job_status(emr_client, job_flow_id)

    if job_status == JobStatus.SUCCESS:
        analysis_result_urls = dict()

        analysis_names = [analysis["analysis_name"] for analysis in analyses]
        analysis_result_paths = get_analysis_result_paths(
            RESULT_BUCKET, result_dir, analysis_names
        )

        for analysis in analyses:
            analysis_name = analysis["analysis_name"]
            analysis_path = analysis_result_paths[analysis_name]
            sub_analyses = analysis["dataset_ids"].keys()
            analysis_result_urls[analysis_name] = dict()

            for sub_analysis in sub_analyses:
                sub_analysis_result_dir = get_sub_analysis_result_dir(
                    analysis_path, sub_analysis, feature_type
                )

                if success_file_exists(sub_analysis_result_dir):
                    object_list = S3_CLIENT.list_objects(
                        Bucket=RESULT_BUCKET, Prefix=sub_analysis_result_dir
                    )
                    keys = [object["Key"] for object in object_list["Contents"]]
                    csv_keys = filter(lambda key: key.endswith(".csv"), keys)

                    analysis_result_urls[analysis_name][sub_analysis] = [
                        "https://{}.s3.amazonaws.com/{}".format(RESULT_BUCKET, key)
                        for key in csv_keys
                    ]
                else:
                    # send slack message
                    slack_webhook("ERROR", error_message)
                    return {"status": "FAILED"}

            upload_results_to_datasets(analyses, upload_type, analysis_result_urls)
        return {
            "status": "SUCCESS",
            "name": name,
            "analyses": analyses,
            "feature_src": event["feature_src"],
        }
    elif job_status == JobStatus.PENDING:
        event.update({"status": "PENDING"})
        return event
    else:
        slack_webhook("ERROR", error_message)
        return {"status": "FAILED"}


def get_sub_analysis_result_dir(analysis_result_path, sub_analysis_name, feature_type):
    return "{}/{}/{}".format(analysis_result_path, feature_type, sub_analysis_name)


def get_analysis_result_paths(result_bucket, result_directory, analysis_names):
    """
    Analysis result directories are named as <analysis>_<date>_<time>
    This creates a map of each analysis to its directory name so we know where to find
    the results for each analysis.
    """
    # adding '/' to result directory and listing with delimiter '/' will make boto list all the subdirectory
    # prefixes instead of all the actual objects
    response = S3_CLIENT.list_objects(
        Bucket=result_bucket, Prefix=result_directory + "/", Delimiter="/"
    )

    # get prefixes from response and remove trailing '/' for consistency
    analysis_result_paths = [
        prefix["Prefix"][:-1] for prefix in response["CommonPrefixes"]
    ]

    analysis_result_paths = dict()
    for path in analysis_result_paths:
        for analysis in analysis_names:
            if analysis in os.path.basename(path):
                analysis_result_paths[analysis] = path

    return analysis_result_paths


class JobStatus(Enum):
    SUCCESS = "SUCCESS"
    PENDING = "PENDING"
    FAILURE = "FAILURE"


def get_job_status(emr_client, job_flow_id: str) -> JobStatus:
    cluster_description = emr_client.describe_cluster(ClusterId=job_flow_id)
    status = cluster_description["Cluster"]["Status"]

    if status["State"] == "TERMINATED":
        # only update AOIs atomically, so they don't get into a partially updated state if the
        # next nightly batch happens before we can fix partially updated AOIs
        if status["StateChangeReason"]["Code"] == "ALL_STEPS_COMPLETED":
            return JobStatus.SUCCESS
        else:
            return JobStatus.FAILURE
    else:
        return JobStatus.PENDING


def success_file_exists(result_dir):
    try:
        # this will throw exception if success file isn't present
        S3_CLIENT.head_object(
            Bucket=RESULT_BUCKET, Key="{}/_SUCCESS".format(result_dir),
        )

        return True
    except ClientError:
        return False


def upload_results_to_datasets(analyses, upload_type, analysis_result_urls):
    # upload to datasets
    for analysis in analyses:
        for sub_analysis in analysis["dataset_ids"].keys():
            upload_dataset(
                analyses[analysis][sub_analysis],
                analysis_result_urls[analysis][sub_analysis],
                upload_type,
            )
