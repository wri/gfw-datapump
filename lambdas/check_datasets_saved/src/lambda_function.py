import os

from typing import Dict

from datapump_utils.slack import slack_webhook
from datapump_utils.exceptions import (
    MaxRetriesHitException,
    StatusMismatchException,
    FailedDatasetUploadException,
)
from datapump_utils.util import error
from datapump_utils.logger import get_logger
from datapump_utils.dataset import (
    get_dataset,
    get_task,
    upload_dataset,
    delete_task,
    recover_dataset,
)


# environment should be set via environment variable. This can be done when deploying the lambda function.
if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"

MAX_RETRIES = 2
LOGGER = get_logger(__name__)


def handler(event, context):
    name = event["name"]
    dataset_ids = event["dataset_ids"]
    dataset_sources = event["dataset_sources"]
    upload_type = event["upload_type"]

    # keep track of number of retries to upload each dataset
    # this lambda runs on a wait loop so it'll keep getting passed back in
    retries = event["retries"] if "retries" in event else dict()

    # check status of dataset requests
    datasets = [get_dataset(id) for id in dataset_ids.values()]
    tasks = [get_task(ds["taskId"]) for ds in datasets]

    try:
        check_for_upload_issues(
            name, datasets, dataset_sources, tasks, upload_type, retries
        )
    except (
        FailedDatasetUploadException,
        StatusMismatchException,
        MaxRetriesHitException,
    ) as e:
        return error(str(e))

    # if any datasets are still pending, return to wait loop
    if get_datasets_with_status(datasets, "pending"):
        event.update({"status": "PENDING", "retries": retries})
        return event

    # Success! Log any task log warnings and send slack notification
    log_task_log_warnings(datasets, tasks)
    slack_webhook("INFO", "Successfully ran {} summary dataset update".format(name))
    event.update({"status": "SUCCESS"})
    return event


def check_for_upload_issues(
    name, datasets, dataset_sources, tasks, upload_type, retries
):
    # see if any datasets have already failed, and if so immediately exit wait loop and return error
    failed_datasets = get_datasets_with_status(datasets, "failed")
    if failed_datasets:
        raise FailedDatasetUploadException(failed_datasets_error(name, failed_datasets))

    status_mismatches = find_status_mismatches(datasets, tasks)
    if status_mismatches:
        raise StatusMismatchException(mismatched_status_error(status_mismatches))

    # no errors yet - see if any datasets are stuck and need a retry before going back to wait loop
    retry_stuck_datasets(datasets, dataset_sources, tasks, upload_type, retries)


def is_dataset_stuck_on_write(dataset: Dict, task: Dict) -> bool:
    """
    Check if dataset upload is stuck on writing for various reasons.
    """
    # look for bug where elasticsearch has jammed writers
    # we can tell this has happened if the # of reads < # of writes
    if dataset["status"] == "pending" and task["reads"] < task["writes"]:
        LOGGER.warning(
            f"Pending dataset has fewer reads({task['reads']}) than writes({task['writes']}), might be stuck.'"
        )
        return True
    # look bug where dataset says it's saved but the task for the write doesn't exist
    # this means the write never actually happened
    elif dataset["status"] == "saved" and task is None:
        LOGGER.warning(
            f"Saved dataset's corresponding task doesn't exist, so upload may have not occurred.'"
        )
        return True
    elif dataset["status"] == "failed":
        if "Exceeded maximum number of attempts to process message" in task["error"]:
            LOGGER.warning(
                f"Task failed because it was stuck. Retrying. Full error: {task['error']}"
            )
        return True
    else:
        return False


def reset_stuck_dataset(dataset: Dict, task=None) -> None:
    """
    Recover dataset and delete corresponding task if it exists.
    """
    if task:
        delete_task(dataset["taskId"])

    recover_dataset(dataset["id"])


def get_datasets_with_status(datasets, status):
    return list(filter(lambda ds: ds["status"] == status, datasets))


def get_task_log_errors(task):
    return [
        (task_log["id"], task_log["detail"])
        for task_log in task["logs"]
        if "withErrors" in task_log
    ]


def retry_upload_dataset(ds, ds_src, task, upload_type, retries):
    reset_stuck_dataset(ds, task)
    retries[ds["id"]] = retries[ds["id"]] + 1 if ds["id"] in retries else 1

    if ds["id"] in retries and retries[ds["id"]] > MAX_RETRIES:
        raise MaxRetriesHitException(
            f"Upload of dataset {ds['id']} failed after {MAX_RETRIES} retries."
        )

    upload_dataset(ds["id"], ds_src, upload_type)

    # change local status to pending instead of querying API again
    ds["status"] = "pending"


def retry_stuck_datasets(datasets, dataset_sources, tasks, upload_type, retries):
    stuck_on_write_statuses = [
        is_dataset_stuck_on_write(ds, task) for ds, task in zip(datasets, tasks)
    ]
    for ds, ds_src, task, stuck_on_write in zip(
        datasets, dataset_sources, tasks, stuck_on_write_statuses
    ):
        if stuck_on_write:
            retry_upload_dataset(ds, ds_src, task, upload_type, retries)


def log_task_log_warnings(datasets, tasks):
    for ds, task in zip(datasets, tasks):
        # check for errors in the task logs and log them as warnings
        for task_log_id, error_details in get_task_log_errors(task):
            LOGGER.warning(task_log_warning(task, task_log_id, error_details))


def find_status_mismatches(datasets, tasks):
    mismatches = list()

    for ds, task in zip(datasets, tasks):
        # make sure both dataset and write tasks are in saved status
        if ds["status"] == "saved" and task["status"] != "SAVED":
            mismatches.append((ds["id"], task["status"]))

    return mismatches


def get_failed_datasets_ids(failed_datasets):
    return ", ".join([ds["id"] for ds in failed_datasets])


def failed_datasets_error(name, failed_datasets):
    return (
        f"Failed to run {name} summary dataset update. The following datasets returned 'failed' status "
        f"when trying to update in API: {get_failed_datasets_ids(failed_datasets)}"
    )


def mismatched_status_error(mismatches):
    err = ", ".join(
        [
            f"(dataset id: {ds_id}, task status: {task_status}"
            for ds_id, task_status in mismatches
        ]
    )
    return f"There are mismatches between dataset and task status: {err}"


def task_log_warning(task, task_log_id, error_details):
    return f"Error in logs on task {task['id']} with id {task_log_id}: {error_details}"
