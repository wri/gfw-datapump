from moto import mock_emr, mock_s3
import boto3

from geotrellis_summary_update.emr import (
    get_summary_analysis_steps,
    _run_job_flow,
    _instances,
    _configurations,
    _applications,
)


@mock_s3
def test_get_analysis_steps():
    _mock_s3_setup()
    steps = _steps()

    annualupdate_step = steps[0]
    assert annualupdate_step["Name"] == "annualupdate"

    step_args = " ".join(annualupdate_step["HadoopJarStep"]["Args"])
    assert (
        step_args
        == f"spark-submit --deploy-mode cluster --class org.globalforestwatch.summarystats.SummaryMain s3://gfw-pipelines-dev/geotrellis/jars/test2.jar --features s3://my/feature/src --output s3://gfw-pipelines-dev/my/result/dir --feature_type geostore --analysis annualupdate --tcl"
    )

    annualupdate_step = steps[1]
    assert annualupdate_step["Name"] == "gladalerts"

    step_args = " ".join(annualupdate_step["HadoopJarStep"]["Args"])
    assert (
        step_args
        == f"spark-submit --deploy-mode cluster --class org.globalforestwatch.summarystats.SummaryMain s3://gfw-pipelines-dev/geotrellis/jars/test2.jar --features s3://my/feature/src --output s3://gfw-pipelines-dev/my/result/dir --feature_type geostore --analysis gladalerts --glad"
    )


@mock_s3
@mock_emr
def test_submit_job():
    _mock_s3_setup()

    name = "testing"
    master_instance_type = "r4.xlarge"
    worker_instance_type = "r4.xlarge"
    worker_instance_count = 10

    instances = _instances(
        name, master_instance_type, worker_instance_type, worker_instance_count
    )
    applications = _applications()
    configurations = _configurations(worker_instance_count)

    # workaround for this bug with moto: https://github.com/spulec/moto/issues/1708
    del instances["InstanceGroups"][0]["EbsConfiguration"]
    del instances["InstanceGroups"][1]["EbsConfiguration"]

    job_flow_id = _run_job_flow(name, instances, _steps(), applications, configurations)

    assert job_flow_id

    client = boto3.client("emr")
    cluster_description = client.describe_cluster(ClusterId=job_flow_id)["Cluster"]

    assert cluster_description["Ec2InstanceAttributes"] == {
        "Ec2KeyName": "jterry_wri",
        "Ec2SubnetId": "None",
        "Ec2AvailabilityZone": "us-east-1a",
        "IamInstanceProfile": "EMR_EC2_DefaultRole",
        "EmrManagedMasterSecurityGroup": "sg-02bec2e5e2a393046",
        "EmrManagedSlaveSecurityGroup": "sg-0fe3f65c2f2e57681",
        "ServiceAccessSecurityGroup": "None",
        "AdditionalMasterSecurityGroups": [],
        "AdditionalSlaveSecurityGroups": [],
    }

    assert cluster_description["LogUri"] == "s3://gfw-pipelines-dev/geotrellis/logs"

    for config in cluster_description["Configurations"]:
        if config["Classification"] == "spark-defaults":
            assert config["Properties"] == {
                "spark.executor.memory": "6G",
                "spark.driver.memory": "6G",
                "spark.driver.cores": "1",
                "spark.driver.maxResultSize": "3G",
                "spark.rdd.compress": "true",
                "spark.executor.cores": "1",
                "spark.sql.shuffle.partitions": "699",
                "spark.shuffle.spill.compress": "true",
                "spark.shuffle.compress": "true",
                "spark.default.parallelism": "699",
                "spark.shuffle.service.enabled": "true",
                "spark.executor.extraJavaOptions": "-XX:+UseParallelGC -XX:+UseParallelOldGC -XX:OnOutOfMemoryError='kill -9 %p'",
                "spark.executor.instances": "69",
                "spark.yarn.executor.memoryOverhead": "1G",
                "spark.dynamicAllocation.enabled": "false",
                "spark.driver.extraJavaOptions": "-XX:+UseParallelGC -XX:+UseParallelOldGC -XX:OnOutOfMemoryError='kill -9 %p'",
            }


def _mock_s3_setup():
    s3_client = boto3.client("s3")

    s3_client.create_bucket(Bucket="gfw-pipelines-dev")
    with open("test_files/test1.jar", "r") as test1_jar:
        s3_client.upload_fileobj(
            test1_jar, Bucket="gfw-pipelines-dev", Key="geotrellis/jars/test1.jar"
        )

    with open("test_files/test2.jar", "r") as test2_jar:
        s3_client.upload_fileobj(
            test2_jar, Bucket="gfw-pipelines-dev", Key="geotrellis/jars/test2.jar"
        )


def _steps():
    return get_summary_analysis_steps(
        ["annualupdate", "gladalerts"],
        "s3://my/feature/src",
        "geostore",
        "my/result/dir",
    )
