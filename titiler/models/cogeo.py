"""Titiler Metadta models."""

from typing import Any, Dict, Optional, Sequence, Tuple

from pydantic import BaseModel, Field
from rio_tiler.constants import BBox


class IFD(BaseModel):
    """ImageFileDirectory info."""

    Level: int
    Width: int
    Height: int
    Blocksize: Tuple[int, int]
    Decimation: int


class Geo(BaseModel):
    """rio-cogeo validation GEO information."""

    CRS: str
    BoundingBox: BBox
    Origin: Tuple[float, float]
    Resolution: Tuple[float, float]


class Profile(BaseModel):
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


class Info(BaseModel):
    """rio-cogeo Info."""

    Path: str
    Driver: str
    COG: bool
    Compression: Optional[str]
    ColorSpace: Optional[str]
    COG_errors: Optional[Sequence[str]]
    COG_warnings: Optional[Sequence[str]]

    Profile: Profile
    GEO: Geo
    Tags: Dict[str, Any]
    IFD: Sequence[IFD]
