import json
import os
import uuid
from typing import Any, Dict, List

import boto3
from datapump.util.models import DATE_REGEX
from datapump.commands.version_update import RasterVersionUpdateCommand
from datapump.util.models import StrictBaseModel
from fastapi import FastAPI, HTTPException, logger
from mangum import Mangum
from pydantic import Field
# from starlette.exceptions import HTTPException as StarletteHTTPException
# from starlette.responses import JSONResponse

GLAD_START_DATE = "2014-12-31"
GLAD_S2_START_DATE = "2018-12-31"
RADD_START_DATE = "2018-12-31"

app = FastAPI()

# Dataset settings
known_datasets = {
    "umd_glad_landsat_alerts": {
        "start_date": GLAD_START_DATE,
        "tile_set_parameters": {
            "no_data": 0,
            "grid": "10/40000",
            "data_type": "uint16",
            "pixel_meaning": "date_conf"
        },
        "tile_cache_parameters": {
            "max_zoom": 12,
            "symbology": {"type": "date_conf_intensity"}
        }
    },
    "umd_glad_sentinel2_alerts": {
        "start_date": GLAD_S2_START_DATE,
        "tile_set_parameters": {
            "no_data": 0,
            "grid": "10/100000",
            "data_type": "uint16",
            "pixel_meaning": "date_conf",
            "calc": "(A > 0) * (20000 + 10000 * (A > 1) + B + 1461).astype(np.uint16)"
        },
        "tile_cache_parameters": {
            "max_zoom": 14,
            "symbology": {"type": "date_conf_intensity"}
        }
    },
    "wur_radd_alerts": {
        "start_date": RADD_START_DATE,
        "tile_set_parameters": {
            "no_data": 0,
            "grid": "10/100000",
            "data_type": "uint16",
            "pixel_meaning": "date_conf"
        },
        "tile_cache_parameters": {
            "max_zoom": 14,
            "symbology": {"type": "date_conf_intensity"}
        }
    }
}


# Models
class Response(StrictBaseModel):
    data: Dict[str, Any]
    status: str = "success"


class UpdateDatasetIn(StrictBaseModel):
    version: str
    source_uri: List[str]
    max_date: str = Field(
        ...,
        description="End date covered by data",
        regex=DATE_REGEX,
    )

# Error handling
# @app.exception_handler(StarletteHTTPException)
# async def http_exception_handler(request, exc):
#     return JSONResponse(
#         status_code=500,
#         content={"message": f"Oops! {exc.name} did something. There goes a rainbow..."},
#     )


# Helper functions
# def ErrorResponse(status_code: int, status: str, message: str):
#     return {
#         status_code=exc.status_code, content={"status": status, "message": message}
#     )


# Routes
@app.get("/")
async def read_root():
    logger.logger.info("In root route!")
    return {"Hello": "World"}


@app.post(
    "/dataset/{dataset}/update",
    status_code=202,
)
async def update_dataset(
    dataset: str,
    request: UpdateDatasetIn
):

    try:
        logger.logger.info("In update route!")

        dataset_params = known_datasets[dataset]

        command = RasterVersionUpdateCommand(**{
            "command": "could be anything",
            "parameters": {
                "dataset": dataset,
                "version": request.version,
                "content_date_range": {
                    "min": dataset_params["start_date"],
                    "max": request.max_date
                },
                "tile_set_parameters": {
                    **dataset_params["tile_set_parameters"],
                    "source_uri": request.source_uri
                },
                "tile_cache_parameters": dataset_params["tile_cache_parameters"]
            }
        })

        sfn_arn = os.environ.get("SFN_DATAPUMP_ARN")

        logger.logger.info("Hold on to your butts!")

        client = boto3.client('stepfunctions')
        response = client.start_execution(
            stateMachineArn=sfn_arn,
            name=f'execution_{uuid.uuid1()}',
            input=json.dumps(command.dict())
        )
        return {
            "status": "success",
            "data": response
        }
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail={"status": "failed", "data": "Unknown dataset."}
        )


handler = Mangum(app)
