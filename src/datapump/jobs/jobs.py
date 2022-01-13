from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from datapump.util.models import StrictBaseModel
from pydantic import BaseModel, validator


class JobStatus(str, Enum):
    starting = "starting"
    executing = "executing"
    complete = "complete"
    failed = "failed"


class JobStep(str, Enum):
    starting = "starting"


class Job(StrictBaseModel, ABC):
    id: str
    step: str = JobStep.starting
    status: JobStatus = JobStatus.starting
    start_time: Optional[str] = None
    timeout_sec: int = 14400
    retries: int = 0

    @validator("start_time", pre=True, always=True)
    def set_start_time(cls, v):
        return v or datetime.now().isoformat()

    @abstractmethod
    def next_step(self):
        ...


class Partition(BaseModel):
    partition_suffix: str
    start_value: str
    end_value: str


class Partitions(BaseModel):
    partition_type: str
    partition_column: str
    partition_schema: List[Partition]


class Index(BaseModel):
    index_type: str
    column_names: List[str]


class AnalysisResultTable(BaseModel):
    dataset: str
    version: str
    source_uri: List[str]
    indices: Optional[List[Index]] = None
    cluster: Optional[Index] = None
    partitions: Optional[Partitions] = None
    table_schema: List[Dict[str, Any]] = []
    latitude_field: str = ""
    longitude_field: str = ""
