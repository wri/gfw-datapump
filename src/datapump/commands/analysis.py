from enum import Enum
from typing import List

from datapump.util.models import StrictBaseModel


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


class AnalysisCommand(StrictBaseModel):
    command: str

    class AnalysisParameters(StrictBaseModel):
        analysis_version: str
        sync: bool
        geotrellis_version: str
        tables: List[AnalysisInputTable]

    parameters: AnalysisParameters
