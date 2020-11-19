from enum import Enum

from datapump.sync.fire_alerts import process_active_fire_alerts
from datapump.sync.rw_areas import create_1x1_tsv


class SyncType(str, Enum):
    viirs = "viirs"
    modis = "modis"
    glad = "glad"
    rw_areas = "rw_areas"


def sync(type: SyncType, version: str):
    if type == SyncType.rw_areas:
        RWAreasSync.sync(version)


class Sync:
    @staticmethod
    def sync(version: str):
        pass


class ViirsSync(Sync):
    @staticmethod
    def sync(version: str):
        viirs_path = [process_active_fire_alerts("VIIRS")]


class ModisSync(Sync):
    @staticmethod
    def sync(version: str):
        viirs_path = [process_active_fire_alerts("VIIRS")]


class GladSync(Sync):
    @staticmethod
    def sync(version: str):
        pass


class RWAreasSync(Sync):
    @staticmethod
    def sync(version: str):
        create_1x1_tsv(version)