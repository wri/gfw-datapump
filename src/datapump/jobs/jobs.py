from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class JobStatus(str, Enum):
    starting = "starting"
    executing = "executing"
    complete = "complete"
    failed = "failed"


class JobStep(str, Enum):
    starting = "starting"


class Job(BaseModel, ABC):
    id: str
    step: JobStep
    status: JobStatus = JobStatus.starting

    @abstractmethod
    def next_step(self):
        ...


class PartitionSchema(BaseModel):
    partition_type: str
    partition_column: str
    partition_values: List[str]


class AnalysisResultTable(BaseModel):
    dataset: str
    version: str
    source_uri: List[str]
    index_columns: Optional[List[str]] = None
    partitions: Optional[PartitionSchema] = None
    table_schema: List[Dict[str, Any]] = []
