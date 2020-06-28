"""Titiler Metadta models."""


from typing import Any, Dict, List, Tuple, Union

from pydantic import BaseModel, Field

from titiler.models.mosaic import mosaicInfo

NumType = Union[float, int]
BBox = Tuple[NumType, NumType, NumType, NumType]


class cogBounds(BaseModel):
    """Bounding box"""

    bounds: BBox


class cogInfo(mosaicInfo):
    """COG Info."""

    band_metadata: List[Tuple[int, Dict[int, Any]]]

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
