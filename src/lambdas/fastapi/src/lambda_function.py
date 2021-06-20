import json
import os
import uuid
from typing import Any, List

import boto3
from fastapi import FastAPI, HTTPException, logger
from mangum import Mangum
from pydantic import BaseModel, Extra
# from starlette.exceptions import HTTPException as StarletteHTTPException
# from starlette.responses import JSONResponse

app = FastAPI()


# Dataset settings
known_datasets = {
    "glad": {

    },
    "glad_s2": {

    },
    "radd": {
        "command": "could be anything",
        "parameters": {
            "dataset": "wur_radd_alerts",
            "version": "v20210516.4",
            "tile_set_parameters": {
                "source_uri": [
                    "s3://gfw-data-lake-dev/gfw_radd_alerts/v20210516/raw_subset/geotiff/"
                ],
                "no_data": 0,
                "grid": "10/100000",
                "data_type": "uint16",
                "pixel_meaning": "data_conf"
            },
            "tile_cache_parameters": {
                "max_zoom": 14,
                "symbology": {"type": "date_conf_intensity"}
            }
        }
    }
}


# Models
class StrictBaseModel(BaseModel):
    class Config:
        extra = Extra.forbid


class Response(StrictBaseModel):
    data: Any
    status: str = "success"


class UpdateDatasetIn(StrictBaseModel):
    version: str
    source_uri: List[str]

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
        # step_fcn_params = known_datasets[dataset]

        step_fcn_params = {
            "command": "could be anything",
            "parameters": {
                "dataset": "wur_radd_alerts",
                "version": request.version,
                "tile_set_parameters": {
                    "source_uri": request.source_uri,
                    "no_data": 0,
                    "grid": "10/100000",
                    "data_type": "uint16",
                    "pixel_meaning": "data_conf"
                },
                "tile_cache_parameters": {
                    "max_zoom": 14,
                    "symbology": {"type": "date_conf_intensity"}
                }
            }
        }

        sfn_arn = os.environ.get("SFN_DATAPUMP_ARN")

        logger.logger.info("In update route!")
        logger.logger.info(f"SFN ARN: {sfn_arn}")
        logger.logger.info("Hold onto your butts!")

        client = boto3.client('stepfunctions')
        response = client.start_execution(
            stateMachineArn=sfn_arn,
            name=f'execution_{uuid.uuid1()}',
            input=json.dumps(step_fcn_params)
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
