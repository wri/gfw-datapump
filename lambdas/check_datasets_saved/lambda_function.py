import os
import logging

from geotrellis_summary_update.slack import slack_webhook
from geotrellis_summary_update.dataset import get_dataset_status

# environment should be set via environment variable. This can be done when deploying the lambda function.
if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"


def handler(event, context):
    name = event["name"]
    analyses = event["analyses"]

    # check status of dataset requests
    dataset_statuses = dict()
    for sub_analyses in analyses.values():
        for dataset_id in sub_analyses.values():
            dataset_statuses[dataset_id] = get_dataset_status(dataset_id)

    pending_statuses = list(
        filter(lambda status: status == "pending", dataset_statuses.values())
    )
    if pending_statuses:
        event.update({"status": "PENDING"})
        return event

    error_statuses = list(
        filter(lambda id_status: id_status[1] == "failed", dataset_statuses.items())
    )
    if error_statuses:
        error_ids = ", ".join([dataset_id for dataset_id, status in error_statuses])
        error_message = (
            "Failed to run {} summary dataset update. "
            "The following datasets returned 'failed' status "
            "when trying to update in API: {}".format(name, error_ids)
        )

        logging.info(error_message)
        slack_webhook("ERROR", error_message)
        return {"status": "FAILED"}

    # send slack info message
    slack_webhook("INFO", "Successfully ran {} summary dataset update".format(name))
    return {
        "status": "SUCCESS",
        "name": name,
        "feature_src": event["feature_src"],
        "analyses": analyses,
    }
