import os
import json
from .emr_steps import StepList
from datapump_utils.util import get_date_string

WORKER_INSTANCE_TYPES = ["r4.2xlarge", "r5.2xlarge", "m4.2xlarge", "m5.2xlarge"]
MASTER_INSTANCE_TYPE = "r4.2xlarge"


class EMRConfig:
    def __init__(self, worker_count, name):
        self.name = name
        self.output_url = f"s3://{os.environ['S3_BUCKET_PIPELINE']}/geotrellis/results/{name}/{get_date_string()}"
        self.steps = StepList(self.output_url)

        self.instances = {
            "InstanceFleets": [
                {
                    "Name": "geotrellis-master",
                    "InstanceFleetType": "MASTER",
                    "TargetOnDemandCapacity": 1,
                    "InstanceTypeConfigs": [
                        {
                            "InstanceType": MASTER_INSTANCE_TYPE,
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
                        }
                    ],
                },
                {
                    "Name": "geotrellis-cores",
                    "InstanceFleetType": "CORE",
                    "TargetOnDemandCapacity": 1,
                    "InstanceTypeConfigs": [
                        {
                            "InstanceType": MASTER_INSTANCE_TYPE,
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
                        }
                    ],
                },
                {
                    "Name": "geotrellis-tasks",
                    "InstanceFleetType": "TASK",
                    "TargetSpotCapacity": worker_count,
                    "InstanceTypeConfigs": [
                        {
                            "InstanceType": instance_type,
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
                        }
                        for instance_type in WORKER_INSTANCE_TYPES
                    ],
                },
            ],
            "Ec2KeyName": os.environ["EC2_KEY_NAME"],
            "KeepJobFlowAliveWhenNoSteps": True,
            "TerminationProtected": False,
            "Ec2SubnetIds": json.loads(os.environ["PUBLIC_SUBNET_IDS"]),
        }

        self.configurations = [
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
                    "spark.sql.shuffle.partitions": str((70 * worker_count) - 1),
                    "spark.shuffle.spill.compress": "true",
                    "spark.shuffle.compress": "true",
                    "spark.default.parallelism": str((70 * worker_count) - 1),
                    "spark.shuffle.service.enabled": "true",
                    "spark.executor.extraJavaOptions": "-XX:+UseParallelGC -XX:+UseParallelOldGC -XX:OnOutOfMemoryError='kill -9 %p'",
                    "spark.executor.instances": str((7 * worker_count) - 1),
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

        self.applications = [
            {"Name": "Spark"},
            {"Name": "Zeppelin"},
            {"Name": "Ganglia"},
        ]

    def add_step(self, *k, **kwargs):
        self.steps.add_step(*k, **kwargs)

    def to_serializable(self):
        return {
            "Name": self.name,
            "OutputUrl": self.output_url,
            "ReleaseLabel": "emr-5.24.0",
            "VisibleToAllUsers": True,
            "JobFlowRole": os.environ["EMR_INSTANCE_PROFILE"],
            "ServiceRole": os.environ["EMR_SERVICE_ROLE"],
            "LogUri": f"s3://{os.environ['S3_BUCKET_PIPELINE']}/geotrellis/logs",
            "Instances": self.instances,
            "Applications": self.applications,
            "Configurations": self.configurations,
            "Steps": self.steps.to_serializable(),
            "Tags": [
                {"Key": "Project", "Value": "Global Forest Watch"},
                {"Key": "Job", "Value": "GeoTrellis Summary Statistics"},
            ],
        }
