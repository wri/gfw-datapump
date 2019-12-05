import boto3

from geotrellis_summary_update.util import bucket_suffix
from geotrellis_summary_update.s3 import get_s3_path

RESULT_BUCKET = f"gfw-pipelines{bucket_suffix()}"


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
    analysis, feature_url, result_url, jar, feature_type="feature"
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

    return {
        "Name": analysis,
        "ActionOnFailure": "TERMINATE_CLUSTER",
        "HadoopJarStep": {"Jar": "command-runner.jar", "Args": step_args},
    }


def get_summary_analysis_steps(analyses, feature_src, feature_type, result_dir):
    latest_jar = _get_latest_geotrellis_jar()
    steps = []

    for analysis in analyses:
        result_url = get_s3_path(RESULT_BUCKET, result_dir)
        steps.append(
            get_summary_analysis_step(
                analysis, feature_src, result_url, latest_jar, feature_type
            )
        )

    return steps


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
    s3_client = boto3.client("s3")

    response = s3_client.list_objects(Bucket=RESULT_BUCKET, Prefix="geotrellis/jars")
    latest_jar = response["Contents"][-1]["Key"]

    return get_s3_path(RESULT_BUCKET, latest_jar)
