import os
import traceback
import json

from datapump_utils.dataset.dataset import (
    create_dataset,
    update_dataset,
    generate_dataset_name,
)
from datapump_utils.logger import get_logger
from datapump_utils.util import error, get_date_string
from datapump_utils.geotrellis.results import (
    success_file_exists,
    get_result_uris,
)

if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"

LOGGER = get_logger(__name__)
DATASETS = json.loads(os.environ["DATASETS"]) if "DATASETS" in os.environ else dict()


def handler(event, context):
    try:
        result_dir = event["output_url"]
        name = event.get("name", "")
        upload_type = event["upload_type"]
        version = event.get("version", None)
        tcl_year = event.get("tcl_year", None)

        updated_datasets = []
        dataset_result_paths = {}
        for path, ds_id in DATASETS.items():
            results_path = f"{result_dir}/{path}"
            if success_file_exists(results_path):
                dataset_sources = get_result_uris(results_path)

                LOGGER.info(
                    f"Dataset sources for result paths {results_path}\n{dataset_sources}"
                )

                if dataset_sources:
                    if upload_type == "create":
                        ds_name = generate_dataset_name(path, version, tcl_year)
                        ds_id = create_dataset(ds_name, dataset_sources)
                    else:
                        update_dataset(ds_id, dataset_sources, upload_type)

                    updated_datasets.append(ds_id)
                    dataset_result_paths[ds_id] = results_path
            else:
                LOGGER.info(
                    f"Skipping dataset {path} because there are no results present."
                )

        event.update(
            {
                "status": "SUCCESS",
                "dataset_ids": updated_datasets,
                "dataset_result_paths": dataset_result_paths,
            }
        )
        return event
    except Exception:
        return error(
            f"Exception caught while running {name} update: {traceback.format_exc()}"
        )
