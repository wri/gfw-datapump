from enum import Enum
from typing import List, Optional, Any, Dict, Union

from pydantic import StrictInt

from datapump.models.base import StrictBaseModel


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


class RasterTileCacheParameters(StrictBaseModel):
    symbology: Optional[Dict[str, Any]]
    max_zoom: int
