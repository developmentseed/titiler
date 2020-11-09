"Titiler mosaic models"

from typing import List, Optional

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
