"""OGC models."""


from typing import List

from pydantic import AnyHttpUrl, BaseModel

from ..ressources.enums import MimeTypes


class TileMatrixSetLink(BaseModel):
    """
    TileMatrixSetLink model.

    Based on http://docs.opengeospatial.org/per/19-069.html#_tilematrixsets

    """

    href: AnyHttpUrl
    rel: str = "item"
    type: MimeTypes = MimeTypes.json

    class Config:
        """Config for model."""

        use_enum_values = True


class TileMatrixSetRef(BaseModel):
    """
    TileMatrixSetRef model.

    Based on http://docs.opengeospatial.org/per/19-069.html#_tilematrixsets

    """

    id: str
    title: str
    links: List[TileMatrixSetLink]


class TileMatrixSetList(BaseModel):
    """
    TileMatrixSetList model.

    Based on http://docs.opengeospatial.org/per/19-069.html#_tilematrixsets

    """

    tileMatrixSets: List[TileMatrixSetRef]
