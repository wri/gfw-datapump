from typing import List, Union

from datapump.jobs.geotrellis import FireAlertsGeotrellisJob, GeotrellisJob
from datapump.util.models import StrictBaseModel


class ContinueGeotrellisJobsParameters(StrictBaseModel):
    jobs: List[Union[FireAlertsGeotrellisJob, GeotrellisJob]]


class ContinueGeotrellisJobsCommand(StrictBaseModel):
    command: str
    parameters: ContinueGeotrellisJobsParameters
