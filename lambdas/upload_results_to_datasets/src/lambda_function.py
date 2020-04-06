import os

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
    try:
        job_flow_id = event["job_flow_id"]
        analyses = event["analyses"]
        datasets = event["datasets"]
        result_dir = event["result_dir"]
        feature_type = event["feature_type"]
        upload_type = event["upload_type"]
        name = event["name"]

        job_status = get_job_status(job_flow_id)
        if job_status == JobStatus.SUCCESS:
            dataset_result_paths = get_dataset_result_paths(
                result_dir, analyses, datasets, feature_type
            )

            LOGGER.info(f"Dataset result paths: {dataset_result_paths}")

            all_dataset_sources = list()
            dataset_ids = dict()
            for dataset, results_path in dataset_result_paths.items():
                dataset_sources = get_dataset_sources(results_path)

                LOGGER.info(
                    f"Dataset sources for result paths {results_path}\n{dataset_sources}"
                )

                if dataset_sources:
                    dataset_ids[dataset] = upload_dataset(
                        dataset, dataset_sources, upload_type
                    )
                    all_dataset_sources.append(dataset_sources)
                else:
                    LOGGER.info(
                        f"Skipping dataset {dataset} because there are no non-empty results."
                    )

            event.update(
                {
                    "status": "SUCCESS",
                    "dataset_ids": dataset_ids,
                    "dataset_sources": all_dataset_sources,
                }
            )
            return event
        elif job_status == JobStatus.PENDING:
            event.update({"status": "PENDING"})
            return event
        else:
            return error(
                f"Geotrellis failure while running {name} update: cluster with ID={job_flow_id} failed."
            )
    except Exception as e:
        return error(f"Exception caught while running {name} update: {e}")
