from typing import List, Union

from datapump.commands import BaseCommand
from datapump.jobs.geotrellis import FireAlertsGeotrellisJob, GeotrellisJob
from datapump.jobs.version_update import RasterVersionUpdateJob
from datapump.util.models import StrictBaseModel


class ContinueJobsParameters(StrictBaseModel):
    jobs: List[Union[GeotrellisJob, FireAlertsGeotrellisJob, RasterVersionUpdateJob]]


class ContinueJobsCommand(BaseCommand):
    parameters: ContinueJobsParameters
