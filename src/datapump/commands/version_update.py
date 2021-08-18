from enum import Enum
from typing import Any, Dict, List, Optional, Union

from datapump.util.models import StrictBaseModel
from pydantic import StrictInt


class NonNumericFloat(str, Enum):
    nan = "nan"


NoDataType = Union[StrictInt, NonNumericFloat]


class RasterTileSetParameters(StrictBaseModel):
    source_uri: List[str]
    calc: Optional[str]
    grid: str
    data_type: str
    no_data: Optional[Union[List[NoDataType], NoDataType]]
    pixel_meaning: str
    bands: int = 1
    union_bands: bool = False


class RasterTileCacheParameters(StrictBaseModel):
    symbology: Optional[Dict[str, Any]]
    max_zoom: int


class RasterVersionUpdateParameters(StrictBaseModel):
    dataset: str
    version: str
    tile_set_parameters: RasterTileSetParameters
    tile_cache_parameters: Optional[RasterTileCacheParameters] = None


class RasterVersionUpdateCommand(StrictBaseModel):
    command: str
    parameters: RasterVersionUpdateParameters
