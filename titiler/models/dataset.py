"""Titiler Metadta models."""


from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from pydantic import BaseModel, Field

from ..ressources.enums import NodataTypes

NumType = Union[float, int]
BBox = Tuple[NumType, NumType, NumType, NumType]
ColorTuple = Tuple[int, int, int, int]
BandIdxType = Union[str, int]


class Bounds(BaseModel):
    """Dataset Bounding box"""

    bounds: BBox


class Info(Bounds):
    """Dataset Info."""

    band_metadata: List[Tuple[int, Dict]]
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


class Metadata(Info):
    """Dataset metadata and statistics."""

    statistics: Dict[BandIdxType, ImageStatistics]


class CogeoInfoIFD(BaseModel):
    """ImageFileDirectory info."""

    Level: int
    Width: int
    Height: int
    Blocksize: Tuple[int, int]
    Decimation: int


class CogeoInfoGeo(BaseModel):
    """rio-cogeo validation GEO information."""

    CRS: str
    BoundingBox: BBox
    Origin: Tuple[float, float]
    Resolution: Tuple[float, float]


class CogeoInfoProfile(BaseModel):
    """rio-cogeo validation Profile information."""

    Bands: int
    Width: int
    Height: int
    Tiled: bool
    Dtype: str
    Interleave: str
    AlphaBand: bool = Field(..., alias="Alpha Band")
    InternalMask: bool = Field(..., alias="Internal Mask")
    Nodata: Any
    ColorInterp: Sequence[str]
    ColorMap: bool
    Scales: Sequence[float]
    Offsets: Sequence[float]

    class Config:
        """Config for model."""

        extra = "ignore"


class RioCogeoInfo(BaseModel):
    """COG Validation Info."""

    Path: str
    Driver: str
    COG: bool
    Compression: Optional[str]
    ColorSpace: Optional[str]
    COG_errors: Optional[Sequence[str]]
    COG_warnings: Optional[Sequence[str]]

    Profile: CogeoInfoProfile
    GEO: CogeoInfoGeo
    Tags: Dict[str, Any]
    IFD: Sequence[CogeoInfoIFD]
