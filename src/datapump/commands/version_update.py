from enum import Enum
from typing import Any, Dict, List, Optional, Union

from datapump.util.models import ContentDateRange, StrictBaseModel
from pydantic import StrictInt


class NonNumericFloat(str, Enum):
    nan = "nan"


NoDataType = Union[StrictInt, NonNumericFloat]


class RasterTileSetParameters(StrictBaseModel):
    source_uri: Optional[List[str]]
    calc: Optional[str]
    grid: str
    data_type: str
    no_data: Optional[Union[List[NoDataType], NoDataType]]
    pixel_meaning: str
    band_count: int = 1
    union_bands: bool = False
    compute_stats: bool = True
    compute_histogram: bool = False
    timeout_sec: int = 7200
    num_processes: Optional[int] = None
    resampling: str = "nearest"


class RasterTileCacheParameters(StrictBaseModel):
    symbology: Optional[Dict[str, Any]]
    max_zoom: int
    resampling: str = "average"


class RasterVersionUpdateParameters(StrictBaseModel):
    dataset: str
    version: str
    content_date_range: ContentDateRange
    tile_set_parameters: RasterTileSetParameters
    tile_cache_parameters: Optional[RasterTileCacheParameters] = None


class RasterVersionUpdateCommand(StrictBaseModel):
    command: str
    parameters: RasterVersionUpdateParameters


class CogAssetParameters(StrictBaseModel):
    implementation: str
    source_pixel_meaning: str
    blocksize: int
    resampling: str = "mode"
    export_to_gee: bool = False
