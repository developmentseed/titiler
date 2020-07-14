"Titiler mosaic models"

from typing import List, Optional, Tuple

from pydantic import BaseModel


class _MosaicJSONCommon(BaseModel):
    """Common request params for MosaicJSON CRUD operations"""

    files: List[str]
    max_threads: int = 20
    url: str


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
    center: Tuple[float, float, int]
    minzoom: int
    maxzoom: int
    name: str
    quadkeys: List[str]
