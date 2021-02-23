from typing import List, Union
from enum import Enum

from pydantic import BaseModel

from datapump.jobs.jobs import Job


class Analysis(str, Enum):
    """
    Supported analyses to run on datasets
    """

    tcl = ("tcl",)
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


class SyncCommand(BaseModel):
    command: str

    class SyncParameters(BaseModel):
        types: List[SyncType]
        sync_version: str = None
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