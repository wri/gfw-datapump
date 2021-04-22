import json
import pprint

import boto3
import click


@click.command()
@click.option("--execution_arn", help="Execution ARN of step function", required=True)
def pump_data(execution_arn):
    sfn_client = boto3.client("stepfunctions")
    response = sfn_client.describe_execution(executionArn=execution_arn)
    if response["status"] == "RUNNING":
        print("Step function still running, check back layer")
    elif response["status"] == "FAILED":
        print(
            f"FAILURE: Step function failed. Look on S3 to debug. Input for reference:\n{json.loads(response['input'])}"
        )
    elif response["status"] == "SUCCEEDED":
        print("SUCCESS: Step function completed with results:")
        pprint.pprint(json.loads(response["output"])["dataset_ids"])
    else:
        print(f"Unexpected status {response['status']}")


if __name__ == "__main__":
    pump_data()
