from typing import List, Union

from datapump.jobs.geotrellis import FireAlertsGeotrellisJob, GeotrellisJob
from datapump.jobs.version_update import RasterVersionUpdateJob
from pydantic import BaseModel


class ContinueJobsParameters(BaseModel):
    jobs: List[Union[GeotrellisJob, FireAlertsGeotrellisJob, RasterVersionUpdateJob]]


class ContinueJobsCommand(BaseModel):
    command: str
    parameters: ContinueJobsParameters
