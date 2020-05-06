import random
import os

WORKER_INSTANCE_TYPE = "r4.2xlarge"


class EMRConfig:
    def __init__(self, worker_count, name):
        self.name = name
        self.instances = {
            "InstanceGroups": [
                {
                    "Name": "geotrellis-master",
                    "Market": "ON_DEMAND",
                    "InstanceRole": "MASTER",
                    "InstanceType": WORKER_INSTANCE_TYPE,
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
                    "Name": "geotrellis-cores",
                    "Market": "ON_DEMAND",
                    "InstanceRole": "CORE",
                    "InstanceType": WORKER_INSTANCE_TYPE,
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
                    "Name": "geotrellis-tasks",
                    "Market": "SPOT",
                    "InstanceRole": "TASK",
                    "InstanceType": WORKER_INSTANCE_TYPE,
                    "InstanceCount": worker_count,
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
            "Ec2KeyName": os.environ["EC2_KEY_NAME"],
            "KeepJobFlowAliveWhenNoSteps": True,
            "TerminationProtected": False,
            "Ec2SubnetId": random.choice(os.environ["PUBLIC_SUBNET_IDS"]),
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

    def to_serializable(self):
        return {
            "Name": self.name,
            "ReleaseLabel": "emr-5.24.0",
            "VisibleToAllUsers": True,
            "JobFlowRole": os.environ["EMR_INSTANCE_PROFILE"],
            "ServiceRole": os.environ["EMR_SERVICE_ROLE"],
            "LogUri": f"s3://{os.environ['RESULT_BUCKET']}/geotrellis/logs",
            "Instances": self.instances,
            "Applications": self.applications,
            "Configurations": self.applications,
            "Tags": [
                {"Key": "Project", "Value": "Global Forest Watch"},
                {"Key": "Job", "Value": "GeoTrellis Summary Statistics"},
            ],
        }
