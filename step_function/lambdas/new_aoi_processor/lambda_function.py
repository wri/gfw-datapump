from botocore.exceptions import ClientError
import boto3
import datetime

EMR_RESULT_BUCKET = "gfw-data-lake-{}"
EMR_RESULT_PREFIX = "user_aois"
NEW_AOI_BUCKET = "aoi_bucket"
NEW_AOI_PREFIX = "prefix"


def lambda_handler(event, context):
    env = event["env"]

    today = datetime.datetime.today()
    result_dir = "{}{}{}".format(today.year, today.month, today.day)
    result_bucket = EMR_RESULT_BUCKET.format(env)
    result_url = "s3://{}/{}/{}".format(EMR_RESULT_BUCKET, EMR_RESULT_PREFIX, result_dir)

    try:
        s3_client = boto3.client("s3")
        if s3_client.list_objects(Bucket=NEW_AOI_BUCKET, Prefix=NEW_AOI_PREFIX):
            aoi_url = "s3://{}/{}/*.tsv".format(NEW_AOI_BUCKET, NEW_AOI_PREFIX)
            job_flow_id = send_emr_job(aoi_url, result_url, env)
            return {
                "NewAOI": True,
                "result_bucket": result_bucket,
                "result_prefix": EMR_RESULT_PREFIX,
                "env": env,
                "job_flow_id": job_flow_id,
            }
    except ClientError:
        return { "NewAOI": False}  # to do: where does this go to?



def send_emr_job(aoi_url, result_url, env):
    client = boto3.client("emr", region_name="us-east-1")

    instances = {
        "InstanceGroups": [
            {
                "Name": "geotrellis-treecoverloss-master",
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
                "Name": "geotrellis-treecoverloss-cores",
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
        "Ec2KeyName": "tmaschler_wri2",
        "KeepJobFlowAliveWhenNoSteps": False,
        "TerminationProtected": False,
        "Ec2SubnetIds": ["subnet-08458452c1d05713b"],  # TODO is everything here down the same?
        "EmrManagedMasterSecurityGroup": "sg-093d1007a79ed4f27",
        "EmrManagedSlaveSecurityGroup": "sg-04abaf6838e8a06fb",
        "AdditionalMasterSecurityGroups": [
            "sg-d7a0d8ad",
            "sg-001e5f904c9cb7cc4",
            "sg-6c6a5911",
        ],
        "AdditionalSlaveSecurityGroups": ["sg-d7a0d8ad", "sg-6c6a5911"],
    }

    steps = [
        {
            "Name": "treecoverloss-analysis",
            "ActionOnFailure": "TERMINATE_CLUSTER",
            "HadoopJarStep": {
                "Jar": "command-runner.jar",
                "Args": [
                    "spark-submit",
                    "--deploy-mode",
                    "cluster",
                    "--class",
                    "org.globalforestwatch.treecoverloss.TreeLossSummaryMain",
                    "s3://gfw-data-lake-dev/2018_update/spark/jars/treecoverloss-assembly-{}.jar".format(  # TODO change to gfw accounts
                        jar_version  # TODO always get latest jar?
                    ),
                    "--features",
                    aoi_url,
                    "--output",
                    result_url + "/treecoverloss",  # TODO output in special place for daily geoms (e.g. user_dashboards/<date>/<analysis type>)
                ]
            },
        },
        {
            "Name": "gladalert-analysis",
            "ActionOnFailure": "TERMINATE_CLUSTER",
            "HadoopJarStep": {
                "Jar": "command-runner.jar",
                "Args": [
                            "spark-submit",
                            "--deploy-mode",
                            "cluster",
                            "--class",
                            "org.globalforestwatch.treecoverloss.TreeLossSummaryMain",  # TODO change to GLAD
                            "s3://gfw-files/2018_update/spark/jars/treecoverloss-assembly-{}.jar".format(
                                jar_version
                            ),
                            "--features",
                            geoms,
                            "--output",
                            "s3://gfw-files/2018_update/results",
                            "--tcd",  # TODO different params|
                            str(tcd_year),
                        ]
            },
        },
    ]

    if primary_forests:  # TODO ...both?
        steps[0]["HadoopJarStep"]["Args"].append("--primary-forests")

    applications = [{"Name": "Spark"}, {"Name": "Zeppelin"}, {"Name": "Ganglia"}]  # TODO same?

    configurations = [
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
                "spark.sql.shuffle.partitions": "{}".format(
                    (70 * worker_instance_count) - 1
                ),
                "spark.shuffle.spill.compress": "true",
                "spark.shuffle.compress": "true",
                "spark.default.parallelism": "{}".format(
                    (70 * worker_instance_count) - 1
                ),
                "spark.shuffle.service.enabled": "true",
                "spark.executor.extraJavaOptions": "-XX:+UseParallelGC -XX:+UseParallelOldGC -XX:OnOutOfMemoryError='kill -9 %p'",
                "spark.executor.instances": "{}".format(
                    (7 * worker_instance_count) - 1
                ),
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

    response = client.run_job_flow(
        Name="Geotrellis Forest Loss Analysis",
        LogUri="s3://gfw-files/2018_update/spark/logs",  # TODO change to location in new GFW
        ReleaseLabel="emr-5.24.0",
        Instances=instances,
        Steps=steps,
        Applications=applications,
        Configurations=configurations,
        VisibleToAllUsers=True,
        JobFlowRole="EMR_EC2_DefaultRole",
        ServiceRole="EMR_DefaultRole",
        Tags=[
            {"Key": "Project", "Value": "Global Forest Watch"},
            {"Key": "Job", "Value": "Tree Cover Loss Analysis"},
        ],
    )

    messages.addMessage(response)
    return