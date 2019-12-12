import os

import boto3
from moto import mock_emr, mock_s3, mock_secretsmanager

from datapump_utils.util import get_curr_date_dir_name, bucket_suffix
from datapump_utils.summary_analysis import (
    get_summary_analysis_steps,
    get_analysis_result_paths,
    check_analysis_success,
    get_dataset_result_paths,
    get_dataset_sources,
    _run_job_flow,
    _instances,
    _configurations,
    _applications,
)

from tests.mock_environment.mock_environment import mock_environment

CURDIR = os.path.dirname(__file__)


@mock_s3
@mock_secretsmanager
def test_get_analysis_steps():
    mock_environment()
    steps = _steps()

    annualupdate_step = steps[0]
    assert annualupdate_step["Name"] == "annualupdate"

    step_args = " ".join(annualupdate_step["HadoopJarStep"]["Args"])
    assert (
        step_args
        == f"spark-submit --deploy-mode cluster --class org.globalforestwatch.summarystats.SummaryMain s3://gfw-pipelines{bucket_suffix()}/geotrellis/jars/test2.jar --features s3://my/feature/src --output s3://gfw-pipelines{bucket_suffix()}/my/result/dir --feature_type geostore --analysis annualupdate --tcl"
    )

    annualupdate_step = steps[1]
    assert annualupdate_step["Name"] == "gladalerts"

    step_args = " ".join(annualupdate_step["HadoopJarStep"]["Args"])
    assert (
        step_args
        == f"spark-submit --deploy-mode cluster --class org.globalforestwatch.summarystats.SummaryMain s3://gfw-pipelines{bucket_suffix()}/geotrellis/jars/test2.jar --features s3://my/feature/src --output s3://gfw-pipelines{bucket_suffix()}/my/result/dir --feature_type geostore --analysis gladalerts --glad"
    )


@mock_s3
@mock_emr
@mock_secretsmanager
def test_submit_job_and_get_status():
    mock_environment()

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

    assert (
        cluster_description["Ec2InstanceAttributes"]
        == TEST_CLUSTER_DESCRIPTION["Cluster"]["Ec2InstanceAttributes"]
    )
    assert (
        cluster_description["LogUri"] == TEST_CLUSTER_DESCRIPTION["Cluster"]["LogUri"]
    )
    assert (
        cluster_description["Configurations"]
        == TEST_CLUSTER_DESCRIPTION["Cluster"]["Configurations"]
    )


@mock_s3
@mock_secretsmanager
def test_get_analysis_result_paths():
    mock_environment()

    result_paths = get_analysis_result_paths(
        f"gfw-pipelines{bucket_suffix()}",
        f"geotrellis/results/test/{get_curr_date_dir_name()}",
        ["gladalerts", "annualupdate_minimal"],
    )

    assert (
        result_paths["gladalerts"]
        == f"geotrellis/results/test/{get_curr_date_dir_name()}/gladalerts_20191119_1245"
    )
    assert (
        result_paths["annualupdate_minimal"]
        == f"geotrellis/results/test/{get_curr_date_dir_name()}/annualupdate_minimal_20191119_1245"
    )


@mock_s3
@mock_secretsmanager
def test_check_analysis_success():
    mock_environment()

    assert check_analysis_success(
        f"geotrellis/results/test/{get_curr_date_dir_name()}/gladalerts_20191119_1245/geostore/daily_alerts"
    )


@mock_s3
@mock_secretsmanager
def test_get_dataset_sources():
    mock_environment()

    https_path = f"https://gfw-pipelines{bucket_suffix()}.s3.amazonaws.com/geotrellis/results/test/{get_curr_date_dir_name()}/gladalerts_20191119_1245/geostore/daily_alerts"
    sources = get_dataset_sources(
        f"geotrellis/results/test/{get_curr_date_dir_name()}/gladalerts_20191119_1245/geostore/daily_alerts"
    )
    assert len(sources) == 2
    assert sources[0] == f"{https_path}/results1.csv"
    assert sources[1] == f"{https_path}/results2.csv"


@mock_s3
@mock_secretsmanager
def test_get_dataset_result_paths():
    mock_environment()

    analyses = ["gladalerts", "annualupdate_minimal"]
    dataset_ids = {
        "gladalerts": {
            "daily_alerts": "testid_daily_alerts_glad",
            "weekly_alerts": "testid_weekly_alerts_glad",
            "summary": "testid_summary_glad",
        },
        "annualupdate_minimal": {
            "change": "testid_change_tcl",
            "summary": "testid_summary_tcl",
        },
    }

    result_dir = f"geotrellis/results/test/{get_curr_date_dir_name()}"
    feature_type = "geostore"

    dataset_result_paths = get_dataset_result_paths(
        result_dir, analyses, dataset_ids, feature_type
    )

    results_glad = f"geotrellis/results/test/{get_curr_date_dir_name()}/gladalerts_20191119_1245/geostore"
    results_tcl = f"geotrellis/results/test/{get_curr_date_dir_name()}/annualupdate_minimal_20191119_1245/geostore"

    assert (
        dataset_result_paths["testid_daily_alerts_glad"]
        == f"{results_glad}/daily_alerts"
    )
    assert (
        dataset_result_paths["testid_weekly_alerts_glad"]
        == f"{results_glad}/weekly_alerts"
    )
    assert dataset_result_paths["testid_summary_glad"] == f"{results_glad}/summary"

    assert dataset_result_paths["testid_change_tcl"] == f"{results_tcl}/change"
    assert dataset_result_paths["testid_summary_tcl"] == f"{results_tcl}/summary"


def _steps():
    return get_summary_analysis_steps(
        ["annualupdate", "gladalerts"],
        "s3://my/feature/src",
        "geostore",
        "my/result/dir",
        True,
    )


TEST_CLUSTER_DESCRIPTION = {
    "Cluster": {
        "Id": "j-66WHAK96149LU",
        "Name": "testing",
        "Status": {
            "State": "TERMINATED",
            "StateChangeReason": {"Code": "ALL_STEPS_COMPLETED"},
        },
        "Ec2InstanceAttributes": {
            "Ec2KeyName": "jterry_wri",
            "Ec2SubnetId": "None",
            "Ec2AvailabilityZone": "us-east-1a",
            "IamInstanceProfile": "EMR_EC2_DefaultRole",
            "EmrManagedMasterSecurityGroup": "sg-02bec2e5e2a393046",
            "EmrManagedSlaveSecurityGroup": "sg-0fe3f65c2f2e57681",
            "ServiceAccessSecurityGroup": "None",
            "AdditionalMasterSecurityGroups": [],
            "AdditionalSlaveSecurityGroups": [],
        },
        "LogUri": f"s3://gfw-pipelines{bucket_suffix()}/geotrellis/logs",
        "ReleaseLabel": "emr-5.24.0",
        "AutoTerminate": True,
        "TerminationProtected": False,
        "VisibleToAllUsers": True,
        "Applications": [{"Name": "Spark"}, {"Name": "Zeppelin"}, {"Name": "Ganglia"}],
        "Tags": [{"Key": "Project", "Value": "Test"}, {"Key": "Job", "Value": "Test"}],
        "ServiceRole": "EMR_DefaultRole",
        "NormalizedInstanceHours": 0,
        "MasterPublicDnsName": "ec2-184-0-0-1.us-west-1.compute.amazonaws.com",
        "Configurations": [
            {
                "Classification": "spark",
                "Properties": {"maximizeResourceAllocation": "true"},
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
                },
            },
            {
                "Classification": "yarn-site",
                "Properties": {
                    "yarn.nodemanager.pmem-check-enabled": "false",
                    "yarn.resourcemanager.am.max-attempts": "1",
                    "yarn.nodemanager.vmem-check-enabled": "false",
                },
            },
        ],
    },
    "ResponseMetadata": {
        "RequestId": "2690d7eb-ed86-11dd-9877-6fad448a8419",
        "HTTPStatusCode": 200,
        "HTTPHeaders": {
            "server": "amazon.com",
            "x-amzn-requestid": "2690d7eb-ed86-11dd-9877-6fad448a8419",
            "date": "Thu, 05 Dec 2019 15:47:04 UTC",
            "content-type": "application/x-amz-json-1.1",
        },
        "RetryAttempts": 0,
    },
}
