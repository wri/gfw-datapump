from enum import Enum
from typing import List, Optional

from datapump.commands.analysis import AnalysisTable, Analysis
from datapump.util.models import StrictBaseModel


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


class SyncParameters(StrictBaseModel):
    types: List[SyncType]
    sync_version: Optional[str] = None
    tables: List[AnalysisTable] = []


class SyncCommand(StrictBaseModel):
    command: str
    parameters: SyncParameters
