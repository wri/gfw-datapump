from enum import Enum
from typing import List, Optional

from datapump.jobs.jobs import Job
from pydantic import BaseModel


class Analysis(str, Enum):
    """
    Supported analyses to run on datasets
    """

    tcl = "tcl"
    glad = "glad"
    viirs = "viirs"
    modis = "modis"


class AnalysisInputTable(BaseModel):
    """
    Input used to generate analysis table by running an analysis on an existing dataset/version.
    """

    dataset: str
    version: str
    analysis: Analysis


class AnalysisTable(BaseModel):
    """
    Metadata of analysis result table that already exists.
    """

    dataset: str
    analysis_version: str
    analysis: Analysis


class SyncType(str, Enum):
    viirs = "viirs"
    modis = "modis"
    glad = "glad"
    rw_areas = "rw_areas"

    @staticmethod
    def get_sync_types(dataset: str, analysis: Analysis):
        sync_types = []
        try:
            sync_types.append(SyncType[analysis.value])
        except KeyError:
            pass

        if "geostore" in dataset:
            sync_types.append(SyncType.rw_areas)

        return sync_types


class AnalysisCommand(BaseModel):
    command: str

    class AnalysisParameters(BaseModel):
        analysis_version: str
        sync: bool
        geotrellis_version: str
        tables: List[AnalysisInputTable]

    parameters: AnalysisParameters


class ImportCommand(BaseModel):
    command: str

    class ImportParameters(BaseModel):
        dataset: str
        version: str
        source_uri: List[str]
        calc: str
        grid: str
        max_zoom: int

    parameters: ImportParameters


class SyncCommand(BaseModel):
    command: str

    class SyncParameters(BaseModel):
        types: List[SyncType]
        sync_version: Optional[str] = None
        tables: List[AnalysisTable] = []

    parameters: SyncParameters


class ContinueJobsCommand(BaseModel):
    command: str

    class ContinueJobsParameters(BaseModel):
        jobs: List[Job]

    parameters: ContinueJobsParameters


class SetLatestCommand(BaseModel):
    command: str

    class SetLatestParameters(BaseModel):
        analysis_version: str

    parameters: SetLatestParameters
