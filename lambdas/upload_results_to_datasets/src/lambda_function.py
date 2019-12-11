import os
import boto3

from datapump_utils.dataset import upload_dataset
from datapump_utils.logger import get_logger
from datapump_utils.util import error
from datapump_utils.summary_analysis import (
    JobStatus,
    get_job_status,
    check_analysis_success,
    get_dataset_result_paths,
    get_dataset_sources,
)

if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"

LOGGER = get_logger(__name__)


def handler(event, context):
    job_flow_id = event["job_flow_id"]
    analyses = event["analyses"]
    dataset_ids = event["dataset_ids"]
    result_dir = event["result_dir"]
    feature_type = event["feature_type"]
    name = event["name"]
    upload_type = event["upload_type"]

    job_status = get_job_status(job_flow_id)
    if job_status == JobStatus.SUCCESS:
        dataset_result_paths = get_dataset_result_paths(
            result_dir, analyses, dataset_ids, feature_type
        )

        paths_with_no_success_file = list(
            filter(
                lambda path: not check_analysis_success(path),
                dataset_result_paths.values(),
            )
        )

        if paths_with_no_success_file:
            return error(
                f"Summary Update Failure: success file were not present for these analyses: {str(paths_with_no_success_file)}"
            )

        all_dataset_sources = list()
        for dataset_id, results_path in dataset_result_paths.items():
            dataset_sources = get_dataset_sources(results_path)
            upload_dataset(dataset_id, dataset_sources, upload_type)
            all_dataset_sources.append(dataset_sources)

        dataset_ids_flattened = list(dataset_result_paths.keys())
        return {
            "status": "SUCCESS",
            "name": name,
            "analyses": analyses,
            "feature_src": event["feature_src"],
            "upload_type": event["upload_type"],
            "dataset_ids": dataset_ids_flattened,
            "dataset_sources": all_dataset_sources,
        }
    elif job_status == JobStatus.PENDING:
        event.update({"status": "PENDING"})
        return event
    else:
        return error(
            f"Summary Update Failure: Cluster with ID={job_flow_id} failed to complete analysis."
        )
