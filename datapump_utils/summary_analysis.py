import os
from enum import Enum

import boto3
from botocore.exceptions import ClientError

from datapump_utils.util import bucket_suffix
from datapump_utils.s3 import get_s3_path, s3_client

RESULT_BUCKET = f"gfw-pipelines{bucket_suffix()}"


class JobStatus(Enum):
    SUCCESS = "SUCCESS"
    PENDING = "PENDING"
    FAILURE = "FAILURE"


def submit_summary_batch_job(name, steps, instance_type, worker_count):
    master_instance_type = instance_type
    worker_instance_type = instance_type
    worker_instance_count = worker_count

    instances = _instances(
        name, master_instance_type, worker_instance_type, worker_instance_count
    )
    applications = _applications()
    configurations = _configurations(worker_instance_count)

    job_flow_id = _run_job_flow(name, instances, steps, applications, configurations)
    return job_flow_id


def get_summary_analysis_step(
    analysis, feature_url, result_url, jar, feature_type="feature", get_summary=True
):
    step_args = [
        "spark-submit",
        "--deploy-mode",
        "cluster",
        "--class",
        "org.globalforestwatch.summarystats.SummaryMain",
        jar,
        "--features",
        feature_url,
        "--output",
        result_url,
        "--feature_type",
        feature_type,
        "--analysis",
        analysis,
    ]

    if "annualupdate" in analysis:
        step_args.append("--tcl")
    elif analysis == "gladalerts":
        step_args.append("--glad")

    if not get_summary:
        step_args.append("--change_only")

    return {
        "Name": analysis,
        "ActionOnFailure": "TERMINATE_CLUSTER",
        "HadoopJarStep": {"Jar": "command-runner.jar", "Args": step_args},
    }


def get_summary_analysis_steps(
    analyses, feature_src, feature_type, result_dir, get_summary
):
    latest_jar = _get_latest_geotrellis_jar()
    steps = []

    for analysis in analyses:
        result_url = get_s3_path(RESULT_BUCKET, result_dir)
        steps.append(
            get_summary_analysis_step(
                analysis, feature_src, result_url, latest_jar, feature_type, get_summary
            )
        )

    return steps


def get_job_status(job_flow_id: str) -> JobStatus:
    emr_client = boto3.client("emr")
    cluster_description = emr_client.describe_cluster(ClusterId=job_flow_id)
    status = cluster_description["Cluster"]["Status"]

    if status["State"] == "TERMINATED":
        # only update AOIs atomically, so they don't get into a partially updated state if the
        # next nightly batch happens before we can fix partially updated AOIs
        if status["StateChangeReason"]["Code"] == "ALL_STEPS_COMPLETED":
            return JobStatus.SUCCESS
        else:
            return JobStatus.FAILURE
    elif status["State"] == "TERMINATED_WITH_ERRORS":
        return JobStatus.FAILURE
    else:
        return JobStatus.PENDING


def get_analysis_result_paths(result_bucket, result_directory, analysis_names):
    """
    Analysis result directories are named as <analysis>_<date>_<time>
    This creates a map of each analysis to its directory name so we know where to find
    the results for each analysis.
    """
    # adding '/' to result directory and listing with delimiter '/' will make boto list all the subdirectory
    # prefixes instead of all the actual objects
    response = s3_client().list_objects(
        Bucket=result_bucket, Prefix=result_directory + "/", Delimiter="/"
    )

    # get prefixes from response and remove trailing '/' for consistency
    analysis_result_paths = [
        prefix["Prefix"][:-1] for prefix in response["CommonPrefixes"]
    ]

    analysis_result_path_map = dict()
    for path in analysis_result_paths:
        for analysis in analysis_names:
            if analysis in os.path.basename(path):
                analysis_result_path_map[analysis] = path

    return analysis_result_path_map


def check_analysis_success(result_dir):
    try:
        # this will throw exception if success file isn't present
        s3_client().head_object(
            Bucket=RESULT_BUCKET, Key=f"{result_dir}/_SUCCESS",
        )

        return True
    except ClientError:
        return False


def get_dataset_result_path(analysis_result_path, aggregate_name, feature_type):
    return "{}/{}/{}".format(analysis_result_path, feature_type, aggregate_name)


def get_dataset_sources(results_path):
    object_list = s3_client().list_objects(Bucket=RESULT_BUCKET, Prefix=results_path)

    keys = [object["Key"] for object in object_list["Contents"]]
    csv_keys = filter(lambda key: key.endswith(".csv"), keys)

    return [
        "https://{}.s3.amazonaws.com/{}".format(RESULT_BUCKET, key) for key in csv_keys
    ]


def get_dataset_result_paths(result_dir, analyses, datasets, feature_type):
    analysis_result_paths = get_analysis_result_paths(
        RESULT_BUCKET, result_dir, analyses
    )
    dataset_result_paths = dict()

    for analysis in datasets.keys():
        for aggregate in datasets[analysis].keys():
            dataset = datasets[analysis][aggregate]
            dataset_result_paths[dataset] = get_dataset_result_path(
                analysis_result_paths[analysis], aggregate, feature_type
            )

    return dataset_result_paths


def _run_job_flow(name, instances, steps, applications, configurations):
    client = boto3.client("emr", region_name="us-east-1")
    response = client.run_job_flow(
        Name=name,
        ReleaseLabel="emr-5.24.0",
        LogUri=f"s3://{RESULT_BUCKET}/geotrellis/logs",  # TODO should this be param?
        Instances=instances,
        Steps=steps,
        Applications=applications,
        Configurations=configurations,
        VisibleToAllUsers=True,
        JobFlowRole="EMR_EC2_DefaultRole",
        ServiceRole="EMR_DefaultRole",
        Tags=[
            {"Key": "Project", "Value": "Global Forest Watch"},
            {"Key": "Job", "Value": "GeoTrellis Summary Statistics"},
        ],  # flake8 --ignore
    )

    return response["JobFlowId"]


def _instances(name, master_instance_type, worker_instance_type, worker_instance_count):
    return {
        "InstanceGroups": [
            {
                "Name": "{}-master".format(name),
                "Market": "ON_DEMAND",
                "InstanceRole": "MASTER",
                "InstanceType": master_instance_type,
                "InstanceCount": 1,
                "EbsConfiguration": {
                    "EbsBlockDeviceConfigs": [
                        {
                            "VolumeSpecification": {
                                "VolumeType": "gp2",
                                "SizeInGB": 10,
                            },
                            "VolumesPerInstance": 1,
                        }
                    ],
                    "EbsOptimized": True,
                },
            },
            {
                "Name": "{}-cores".format(name),
                "Market": "SPOT",
                "InstanceRole": "CORE",
                # "BidPrice": "0.532",
                "InstanceType": worker_instance_type,
                "InstanceCount": worker_instance_count,
                "EbsConfiguration": {
                    "EbsBlockDeviceConfigs": [
                        {
                            "VolumeSpecification": {
                                "VolumeType": "gp2",
                                "SizeInGB": 10,
                            },
                            "VolumesPerInstance": 1,
                        }
                    ],
                    "EbsOptimized": True,
                },
            },
        ],
        "Ec2KeyName": "jterry_wri",
        "KeepJobFlowAliveWhenNoSteps": False,
        "TerminationProtected": False,
        "Ec2SubnetIds": ["subnet-44dbbd7a"],
        "EmrManagedMasterSecurityGroup": "sg-02bec2e5e2a393046",
        "EmrManagedSlaveSecurityGroup": "sg-0fe3f65c2f2e57681",
        # "AdditionalMasterSecurityGroups": [
        #    "sg-d7a0d8ad",
        #    "sg-001e5f904c9cb7cc4",
        #    "sg-6c6a5911",
        # ],
        # "AdditionalSlaveSecurityGroups": ["sg-d7a0d8ad", "sg-6c6a5911"],
    }


def _applications():
    return [
        {"Name": "Spark"},
        {"Name": "Zeppelin"},
        {"Name": "Ganglia"},
    ]


def _configurations(worker_instance_count):
    return [
        {
            "Classification": "spark",
            "Properties": {"maximizeResourceAllocation": "true"},
            "Configurations": [],
        },
        {
            "Classification": "spark-defaults",
            "Properties": {
                "spark.executor.memory": "6G",
                "spark.driver.memory": "6G",
                "spark.driver.cores": "1",
                "spark.driver.maxResultSize": "3G",
                "spark.rdd.compress": "true",
                "spark.executor.cores": "1",
                "spark.sql.shuffle.partitions": str((70 * worker_instance_count) - 1),
                "spark.shuffle.spill.compress": "true",
                "spark.shuffle.compress": "true",
                "spark.default.parallelism": str((70 * worker_instance_count) - 1),
                "spark.shuffle.service.enabled": "true",
                "spark.executor.extraJavaOptions": "-XX:+UseParallelGC -XX:+UseParallelOldGC -XX:OnOutOfMemoryError='kill -9 %p'",
                "spark.executor.instances": str((7 * worker_instance_count) - 1),
                "spark.yarn.executor.memoryOverhead": "1G",
                "spark.dynamicAllocation.enabled": "false",
                "spark.driver.extraJavaOptions": "-XX:+UseParallelGC -XX:+UseParallelOldGC -XX:OnOutOfMemoryError='kill -9 %p'",
            },
            "Configurations": [],
        },
        {
            "Classification": "yarn-site",
            "Properties": {
                "yarn.nodemanager.pmem-check-enabled": "false",
                "yarn.resourcemanager.am.max-attempts": "1",
                "yarn.nodemanager.vmem-check-enabled": "false",
            },
            "Configurations": [],
        },
    ]


def _get_latest_geotrellis_jar():

    # environment should be set via environment variable. This can be done when deploying the lambda function.
    if "GEOTRELLIS_JAR" in os.environ:
        jar = os.environ["GEOTRELLIS_JAR"]
    else:
        raise ValueError("Environment Variable 'GEOTRELLIS_JAR' is not set")

    return jar
