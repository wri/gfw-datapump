from upload_records.append import _append_records
from botocore.exceptions import ClientError
import boto3

DATASET_ID = "dataset_id"

def lambda_handler(event, context):
    env = event["env"]
    job_flow_id = event["job_flow_id"]
    emr_result_bucket = event["result_bucket"]
    emr_result_prefix = event["result_prefix"]
    analyses = event["analyses"]

    # checks status of job
    emr_client = boto3.client("emr")
    cluster_description = emr_client.describe_cluster(ClusterId=job_flow_id)


    if cluster_description["Cluster"]["Status"]["State"] == "TERMINATED":
        # TODO do we POST if some, but not all, steps completed successfully?
        for analysis in analyses:
            s3_client = boto3.client("s3")
            analysis_result_prefix = "{}/{}".format(emr_result_prefix, analysis)

            try:
                # this will throw exception if success file isn't present
                success_file = s3_client.head_object(Bucket=emr_result_bucket, Key="{}/_SUCCESS".format(analysis_result_prefix))

                object_list = s3_client.list_objects(Bucket=emr_result_bucket, Prefix=analysis_result_prefix)
                keys = [object["Key"] for object in object_list['Contents']]
                csv_keys = filter(lambda key: key.endswith(".csv"), keys)

                s3_urls = ["s3://{}/{}".format(emr_result_bucket, key) for key in csv_keys]

                for s3_url in s3_urls:
                    _append_records(DATASET_ID, s3_url, env)

                return {
                    "EMRComplete": "SUCCESS",
                    "dataset_id": DATASET_ID
                }
            except ClientError:
                # send slack message
                return { "EMRComplete": "FAILED" }
    else:
        return { "EMRComplete": "PENDING" }