"""Titiler Metadta models."""


from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field

from titiler.ressources.enums import NodataTypes

NumType = Union[float, int]
BBox = Tuple[NumType, NumType, NumType, NumType]
ColorTuple = Tuple[int, int, int, int]


class cogBounds(BaseModel):
    """Bounding box"""

    bounds: BBox


class cogInfo(BaseModel):
    """COG Info."""

    bounds: Tuple[float, float, float, float]
    band_metadata: List[Tuple[int, Dict[int, Any]]]
    band_descriptions: List[Tuple[int, str]]
    dtype: str
    colorinterp: List[str]
    nodata_type: NodataTypes
    scale: Optional[float]
    offsets: Optional[float]
    colormap: Optional[Dict[int, ColorTuple]]

    class Config:
        """Config for model."""

        extra = "ignore"
        use_enum_values = True


class ImageStatistics(BaseModel):
    """Image statistics"""

    percentiles: List[NumType] = Field(..., alias="pc")
    min: NumType
    max: NumType
    std: NumType
    histogram: List[List[NumType]]


class cogMetadata(cogInfo):
    """COG metadata and statistics."""

    statistics: Dict[int, ImageStatistics]
