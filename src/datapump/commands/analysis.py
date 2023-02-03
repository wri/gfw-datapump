from enum import Enum
from typing import List

from ..globals import GLOBALS
from ..util.models import StrictBaseModel


class Analysis(str, Enum):
    """
    Supported analyses to run on datasets
    """

    tcl = "tcl"
    glad = "glad"
    viirs = "viirs"
    modis = "modis"
    burned_areas = "burned_areas"
    integrated_alerts = "integrated_alerts"
    create_raster = "create_raster"


FIRES_ANALYSES = [Analysis.viirs, Analysis.modis, Analysis.burned_areas]


class AnalysisInputTable(StrictBaseModel):
    """
    Input used to generate analysis table by running an analysis on an existing dataset/version.
    """

    dataset: str
    version: str
    analysis: Analysis


class IsoRange(StrictBaseModel):
    iso_start: str
    iso_end: str


class AnalysisTable(StrictBaseModel):
    """
    Metadata of analysis result table that already exists.
    """

    dataset: str
    analysis_version: str
    analysis: Analysis
    iso_range: IsoRange = IsoRange(
        iso_start=GLOBALS.geotrellis_iso_start, iso_end=GLOBALS.geotrellis_iso_end
    )


class AnalysisParameters(StrictBaseModel):
    analysis_version: str
    sync: bool
    geotrellis_version: str
    tables: List[AnalysisInputTable]


class AnalysisCommand(StrictBaseModel):
    command: str
    parameters: AnalysisParameters
