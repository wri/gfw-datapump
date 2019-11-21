from summary_analysis_batch.utils import slack_webhook

import requests
import json

def handler(event, context):
    name = event["name"]
    env = event["env"]
    analyses = event["analyses"]

    # check status of dataset requests
    dataset_statuses = dict()
    for sub_analyses in analyses.values():
        for dataset_id in sub_analyses.values():
            dataset_statuses[dataset_id] = get_dataset_status(dataset_id, env)

    pending_statuses = list(filter(lambda status: status == "pending", dataset_statuses.values()))
    if pending_statuses:
        return {"status": "PENDING"}

    error_statuses = list(filter(lambda id_status: id_status[1] == "failed", dataset_statuses.items()))
    if error_statuses:
        error_ids = ', '.join([dataset_id for dataset_id, status in error_statuses])
        error_message = "Failed to run {} summary dataset update. " \
                        "The following datasets returned 'failed' status " \
                        "when trying to update in API: {}".format(name, error_ids)

        slack_webhook("ERROR", error_message, env)
        return {"status": "FAILED"}

    # send slack info message
    slack_webhook("INFO", "Successfully ran {} summary dataset update".format(name), env)
    return {
        "status": "SUCCESS",
        "name": name,
        "env": env,
        "feature_src": event["feature_src"],
        "analyses": analyses
    }


def get_dataset_status(dataset_id, env):
    url = "https://{}-api.globalforestwatch.org/v1/dataset/{}".format(env, dataset_id)
    response = requests.get(url)
    response_json = json.loads(response.text)
    return response_json["data"]["attributes"]["status"]


if __name__ == "__main__":
    print(handler({
        "env": "staging",
        "name": "new_area_test",
        "feature_src": "s3://gfw-pipelines-dev/geotrellis/features/*.tsv",
        "analyses": {
            "gladalerts": {
                "daily_alerts": "72af8802-df3c-42ab-a369-5e7f2b34ae2f",
                #"weekly_alerts": "Glad Alerts - Weekly - Geostore - User Areas",
                #"summary": "Glad Alerts - Summary - Geostore - User Areas",
            }
        }
    }, None))
