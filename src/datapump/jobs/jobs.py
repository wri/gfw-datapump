from enum import Enum
from typing import List, Dict, Any

from pydantic import BaseModel


class JobStatus(str, Enum):
    starting = "starting"
    analyzing = "analyzing"
    analyzed = "analyzed"
    uploading = "uploading"
    complete = "complete"
    failed = "failed"


class Job(BaseModel):
    id: str
    status: JobStatus = JobStatus.starting


class PartitionSchema(BaseModel):
    partition_type: str
    partition_column: str
    partition_values: List[str]


class AnalysisResultTable(BaseModel):
    dataset: str
    version: str
    source_uri: List[str]
    index_columns: List[str] = None
    partitions: PartitionSchema = None
    table_schema: List[Dict[str, Any]] = {}
