from typing import Dict, Any, List
from enum import Enum
from pydantic import BaseModel

"""
{
    "version": "v2020Q2",
    "reporting_dataset": "wdpa_protected_areas",
    "analysis": "tcl",
    "geotrellis_jar_version": "1.2.0",
    "sync": true,
    "depends_on": "",
    "raster_versions": {
        "umd_tree_cover_loss": "v1.7",
        "umd_tree_cover_density_2000": "v1.6",
    }
"""


class Analysis(str, Enum):
    tcl = "annualupdate_minimal"
    glad = "gladalerts"
    viirs = "firealerts_viirs"
    modis = "firealerts_modis"


class ZonalStatsTable(BaseModel):
    dataset: str
    analysis: Analysis


class RasterVersion:
    name: str
    version: str


class DataPumpStore:
    CLIENT = ""

    def __init__(self, raster_versions: List[RasterVersion]):
        self.raster_versions = raster_versions

    def create_new_version(self, version: str, tables: List[ZonalStatsTable]) -> None:
        """
        Create entries for each table in new version
        :param version: New version
        :param tables: List of all tables to include in version
        :return: None
        """
        try:
            successful_tables = []
            for table in tables:
                successful_tables.append(self.create_new_table(version, table))
        except Exception as e:
            # rollback added tables in case of error
            for table in successful_tables:
                self.delete_table(version, table)

            raise e

    def create_new_table(self, version: str, table: ZonalStatsTable) -> None:
        pass

    def delete_table(self, version: str, table: ZonalStatsTable) -> None:
        pass

    def update(self):
        pass
