from typing import List

from datapump.jobs.jobs import Job
from datapump.util.models import StrictBaseModel


class ContinueJobsCommand(StrictBaseModel):
    command: str

    class ContinueJobsParameters(StrictBaseModel):
        jobs: List[Job]

    parameters: ContinueJobsParameters
