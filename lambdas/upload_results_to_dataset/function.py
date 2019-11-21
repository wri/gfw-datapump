from upload_records.aws import get_api_token
from botocore.exceptions import ClientError
from summary_analysis_batch.utils import slack_webhook
import boto3
import requests
import json
import os


def handler(event, context):
    env = event["env"]
    job_flow_id = event["job_flow_id"]
    analyses = event["analyses"]
    result_bucket = event["result_bucket"]
    result_dir = event["result_dir"]
    feature_type = event["feature_type"]
    name = event["name"]

    # checks status of job
    emr_client = boto3.client("emr")
    cluster_description = emr_client.describe_cluster(ClusterId=job_flow_id)
    status = cluster_description["Cluster"]["Status"]

    error_message = "Failed to update {} summary datasets. Cluster with ID={} failed to complete analysis.".format(name, job_flow_id)

    if status["State"] == "TERMINATED":
        # only update AOIs atomically, so they don't get into a partially updated state if the
        # next nightly batch happens before we can fix partially updated AOIs
        if status["StateChangeReason"]["Code"] != "ALL_STEPS_COMPLETED":
            slack_webhook("ERROR", error_message, env)
            return {"status": "FAILED"}

        s3_client = boto3.client("s3")
        analysis_result_urls = dict()

        analysis_names = analyses.keys()
        analysis_result_map = get_analysis_result_map(result_bucket, result_dir, analysis_names, s3_client)

        for analysis_name in analysis_names:
            analysis_path = analysis_result_map[analysis_name]
            sub_analyses = analyses[analysis_name].keys() # get_analysis_result_dirs(analysis_name, analysis_path, feature_type)
            analysis_result_urls[analysis_name] = dict()

            for sub_analysis in sub_analyses:
                try:
                    sub_analysis_result_dir = get_sub_analysis_result_dir(analysis_path, sub_analysis, feature_type)

                    # this will throw exception if success file isn't present
                    success_file = s3_client.head_object(
                        Bucket=result_bucket,
                        Key="{}/_SUCCESS".format(sub_analysis_result_dir)
                    )

                    object_list = s3_client.list_objects(Bucket=result_bucket, Prefix=sub_analysis_result_dir)
                    keys = [object["Key"] for object in object_list['Contents']]
                    csv_keys = filter(lambda key: key.endswith(".csv"), keys)

                    analysis_result_urls[analysis_name][sub_analysis] = [
                        "https://{}.s3.amazonaws.com/{}".format(result_bucket, key)
                        for key in csv_keys
                    ]
                except ClientError:
                    # send slack message
                    slack_webhook("ERROR", error_message, env)
                    return {"status": "FAILED"}

        # concat to each datastore
        for analysis in analyses.keys():
            for sub_analysis in analyses[analysis].keys():
                concat_dataset(
                    analyses[analysis][sub_analysis],
                    analysis_result_urls[analysis][sub_analysis],
                    env
                )

        return {
            "status": "SUCCESS",
            "name": name,
            "env": env,
            "analyses": analyses,
            "feature_src": event["feature_src"]
        }

    else:
        return {"status": "PENDING"}


def get_sub_analysis_result_dir(analysis_result_path, sub_analysis_name, feature_type):
    return "{}/{}/{}".format(analysis_result_path, feature_type, sub_analysis_name)


def get_analysis_result_map(result_bucket, result_directory, analysis_names, s3_client):
    """
    Analysis result directories are named as <analysis>_<date>_<time>

    This creates a map of each analysis to its directory name so we know where to find
    the results for each analysis.
    """
    # adding '/' to result directory and listing with delimiter '/' will make boto list all the subdirectory
    # prefixes instead of all the actual objects
    response = s3_client.list_objects(Bucket=result_bucket, Prefix=result_directory + '/', Delimiter='/')

    # get prefixes from response and remove trailining '/' for consistency
    analysis_result_paths = [prefix['Prefix'][:-1] for prefix in response['CommonPrefixes']]

    analysis_result_map = dict()
    for path in analysis_result_paths:
        for analysis in analysis_names:
            if analysis in os.path.basename(path):
                analysis_result_map[analysis] = path

    return analysis_result_map


def create_dataset(dataset_id, source_urls, env="production"):
    url = "https://{}-api.globalforestwatch.org/v1/dataset".format(env)
    token = get_api_token(env)

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(token),
    }

    payload = {
        "provider": "tsv",
        "connectorType": "document",
        "application": ["gfw"],
        "name": dataset_id,
        "sources": source_urls
    }

    r = requests.post(url, data=json.dumps(payload), headers=headers)

    if r.status_code != 204:
        raise Exception(
            "Data upload failed - received status code {}: "
            "Message: {}".format(r.status_code, r.json)
        )


def concat_dataset(dataset_id, source_urls, env="production"):
    url = "https://{}-api.globalforestwatch.org/v1/dataset/{}/concat".format(env, dataset_id)
    token = get_api_token(env)

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(token),
    }

    payload = {"provider": "csv", "sources": source_urls}

    r = requests.post(url, data=json.dumps(payload), headers=headers)

    if r.status_code != 204:
        raise Exception(
            "Data upload failed - received status code {}: "
            "Message: {}".format(r.status_code, r.json)
        )