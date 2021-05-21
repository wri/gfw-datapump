from enum import Enum
from typing import List, Optional

from datapump.jobs.jobs import Job
from pydantic import BaseModel, Extra


class StrictBaseModel(BaseModel):
    class Config:
        extra = Extra.forbid


class Analysis(str, Enum):
    """
    Supported analyses to run on datasets
    """

    tcl = "tcl"
    glad = "glad"
    viirs = "viirs"
    modis = "modis"


class AnalysisInputTable(StrictBaseModel):
    """
    Input used to generate analysis table by running an analysis on an existing dataset/version.
    """

    dataset: str
    version: str
    analysis: Analysis


class AnalysisTable(StrictBaseModel):
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


class UpdatableDatasets(str, Enum):
    wur_radd_alerts = "wur_radd_alerts"
    umd_glad_sentinel2_alerts = "umd_glad_sentinel2_alerts"


class AnalysisCommand(StrictBaseModel):
    command: str

    class AnalysisParameters(StrictBaseModel):
        analysis_version: str
        sync: bool
        geotrellis_version: str
        tables: List[AnalysisInputTable]

    parameters: AnalysisParameters


class VersionUpdateCommand(StrictBaseModel):
    command: str

    class VersionUpdateParameters(StrictBaseModel):
        dataset: str
        version: str
        source_uri: List[str]

    parameters: VersionUpdateParameters


class SyncCommand(StrictBaseModel):
    command: str

    class SyncParameters(StrictBaseModel):
        types: List[SyncType]
        sync_version: Optional[str] = None
        tables: List[AnalysisTable] = []

    parameters: SyncParameters


class ContinueJobsCommand(StrictBaseModel):
    command: str

    class ContinueJobsParameters(StrictBaseModel):
        jobs: List[Job]

    parameters: ContinueJobsParameters


class SetLatestCommand(StrictBaseModel):
    command: str

    class SetLatestParameters(StrictBaseModel):
        analysis_version: str

    parameters: SetLatestParameters
