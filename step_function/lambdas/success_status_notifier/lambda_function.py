from upload_records.tasks import get_task_log
from upload_records.errors import DatasetFailedError, DatasetPendingError

def lambda_handler(event, context):
    # check status of POST
    try:
        get_task_log(event["dataset_id"])

        # send notification to subscription service
        update_subscription_service()

        # send slack info message
        # delete folders??
    except DatasetPendingError:
        return {"status": "waiting"}
    except DatasetFailedError:
        # send slack error emssage
        return

    return

def update_subscription_service():
    return