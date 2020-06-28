"Titiler mosaic models"

from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel

from titiler.ressources.enums import NodataTypes

ColorTuple = Tuple[int, int, int, int]


class _MosaicJSONCommon(BaseModel):
    """Common request params for MosaicJSON CRUD operations"""

    files: List[str]
    url: str
    max_threads: int = 20


class CreateMosaicJSON(_MosaicJSONCommon):
    """Request body for MosaicJSON creation"""

    minzoom: Optional[int] = None
    maxzoom: Optional[int] = None


class UpdateMosaicJSON(_MosaicJSONCommon):
    """Request body for updating an existing MosaicJSON"""

    add_first: bool = True


class mosaicInfo(BaseModel):
    """MosaicJSON info."""

    bounds: Tuple[float, float, float, float]
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
