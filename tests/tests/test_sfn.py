import boto3
import json
import time
from pprint import pprint

LOCALSTACK_URI = "http://localhost:4566"
DATAPUMP_SFN_ARN = (
    "arn:aws:states:us-east-1:000000000000:stateMachine:datapump-datapump-default"
)


def test_datapump_update():
    try:
        start_time = time.time()

        input = {
            "command": "update",
            "parameters": {
                "version": "vteststats1",
                "tables": [
                    {
                        "dataset": "test_zonal_stats",
                        "version": "vtest1",
                        "analysis": "tcl",
                    },
                    {
                        "dataset": "test_zonal_stats",
                        "version": "vtest1",
                        "analysis": "glad",
                    },
                ],
            },
        }

        _tests_datapump(input, "SUCCEEDED")
        assert False
    finally:
        _dump_logs(start_time)


def _dump_logs(start_time):
    sfn_client = boto3.client("stepfunctions", endpoint_url=LOCALSTACK_URI)
    log_client = boto3.client("logs", endpoint_url=LOCALSTACK_URI)

    resp = sfn_client.list_executions(stateMachineArn=DATAPUMP_SFN_ARN)
    execution_arn = resp["executions"][-1]["executionArn"]

    resp = sfn_client.get_execution_history(executionArn=execution_arn)
    pprint(resp["events"])

    for log_group in log_client.describe_log_groups()["logGroups"]:
        log_group_name = log_group["logGroupName"]
        print(
            f"---------------------------- {log_group_name} ---------------------------------"
        )
        # for log_stream in log_client.describe_log_streams(logGroupName=log_group_name)['logStreams']:
        # if log_stream['lastEventTimestamp'] / 1000 > start_time:
        log_streams = log_client.describe_log_streams(logGroupName=log_group_name)[
            "logStreams"
        ]
        log_stream_name = log_streams[-1]["logStreamName"]
        log_events = log_client.get_log_events(
            logGroupName=log_group_name,
            logStreamName=log_stream_name,
            # startTime=int(start_time * 1000)
        )["events"]

        for event in log_events:
            # for some reason stack traces come with carriage returns,
            # which overwrites the line instead of making a new line
            message = event["message"].replace("\r", "\n")
            print(f"{log_stream_name}: {message}")


def _tests_datapump(input, expected_status):
    client = boto3.client("stepfunctions", endpoint_url=LOCALSTACK_URI)

    resp = client.start_execution(
        stateMachineArn=DATAPUMP_SFN_ARN, input=json.dumps(input)
    )

    execution_arn = resp["executionArn"]
    print(execution_arn)

    tries = 0
    while tries < 30:
        time.sleep(2)
        tries += 1

        status = client.describe_execution(executionArn=execution_arn)["status"]
        if status == "RUNNING":
            continue
        else:
            assert status == expected_status
