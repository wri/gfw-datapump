import boto3
from botocore.exceptions import ClientError
import json
import time
import sys
import os
from pprint import pprint


LOCALSTACK_URI = "http://localstack:4566"
DATAPUMP_SFN_ARN = (
    "arn:aws:states:us-east-1:000000000000:stateMachine:datapump-datapump-default"
)
DUMP_TO_STDOUT = os.environ.get("DUMP_TO_STDOUT", None)


def test_datapump():
    try:
        add_version_input = {
            "command": "analysis",
            "parameters": {
                "analysis_version": "vteststats1",
                "geotrellis_version": "1.2.1",
                "sync": True,
                "tables": [
                    {
                        "dataset": "test_zonal_stats",
                        "version": "vtest1",
                        "analysis": "glad",
                    }
                ],
            },
        }

        status = _run_datapump(add_version_input)
        assert status == "SUCCEEDED"

        sync_input = {
            "command": "sync",
            "parameters": {"types": ["glad"], "sync_version": "v20210122"},
        }

        status = _run_datapump(sync_input)
        assert status == "SUCCEEDED"
    finally:
        _dump_logs()


def _dump_logs():
    sfn_client = boto3.client("stepfunctions", endpoint_url=LOCALSTACK_URI)
    log_client = boto3.client("logs", endpoint_url=LOCALSTACK_URI)
    emr_client = boto3.client("emr", endpoint_url=LOCALSTACK_URI)
    s3_client = boto3.client("s3", endpoint_url=LOCALSTACK_URI)

    if DUMP_TO_STDOUT:
        sfn_stream, emr_stream, lambda_stream = sys.stdout, sys.stdout, sys.stdout
    else:
        sfn_stream = open("/app/tests/logs/stepfunction.log", "w")
        emr_stream = open("/app/tests/logs/emr.log", "w")
        lambda_stream = open("/app/tests/logs/lambdas.log", "w")

    #### Step Function
    resp = sfn_client.list_executions(stateMachineArn=DATAPUMP_SFN_ARN)
    execution_arn = resp["executions"][-1]["executionArn"]
    resp = sfn_client.get_execution_history(executionArn=execution_arn)
    pprint(resp["events"], stream=sfn_stream)

    #### EMR
    clusters = emr_client.list_clusters()["Clusters"]
    pprint(clusters, stream=emr_stream)

    for cluster in clusters:
        pprint(emr_client.describe_cluster(ClusterId=cluster["Id"]), stream=emr_stream)

    #### Lambda
    for log_group in log_client.describe_log_groups()["logGroups"]:
        log_group_name = log_group["logGroupName"]
        print(
            f"---------------------------- {log_group_name} ---------------------------------",
            file=lambda_stream,
        )
        for log_stream in log_client.describe_log_streams(logGroupName=log_group_name)[
            "logStreams"
        ]:
            log_events = log_client.get_log_events(
                logGroupName=log_group_name,
                logStreamName=log_stream["logStreamName"],
            )["events"]

            for event in log_events:
                # for some reason stack traces come with carriage returns,
                # which overwrites the line instead of making a new line
                message = event["message"].replace("\r", "\n")
                print(f"{log_stream['logStreamName']}: {message}", file=lambda_stream)

    if not DUMP_TO_STDOUT:
        try:
            s3_client.download_file(
                "gfw-pipelines-test", "datapump/config.db", "/app/tests/logs/config.db"
            )
        except ClientError:
            print("config.db not available")


def _run_datapump(input):
    client = boto3.client("stepfunctions", endpoint_url=LOCALSTACK_URI)

    resp = client.start_execution(
        stateMachineArn=DATAPUMP_SFN_ARN, input=json.dumps(input)
    )

    execution_arn = resp["executionArn"]
    print(execution_arn)

    tries = 0
    while tries < 3000:
        time.sleep(2)
        tries += 1

        status = client.describe_execution(executionArn=execution_arn)["status"]
        if status == "RUNNING":
            continue
        else:
            return status
