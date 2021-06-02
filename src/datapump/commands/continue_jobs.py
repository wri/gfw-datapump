from typing import List

from datapump.jobs.jobs import Job
from datapump.util.models import StrictBaseModel


class ContinueJobsParameters(StrictBaseModel):
    jobs: List[Job]


class ContinueJobsCommand(StrictBaseModel):
    command: str
    parameters: ContinueJobsParameters
