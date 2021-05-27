"""Titiler.mosaic Models."""

from cogeo_mosaic.mosaic import MosaicJSON
from typing import List, Optional

from stac_pydantic.api import Search
from pydantic import BaseModel


def to_camel(snake_str: str) -> str:
    """
    Converts snake_case_string to camelCaseString
    """
    first, *others = snake_str.split("_")
    return "".join([first.lower(), *map(str.title, others)])


# Link and Links derived from models in https://github.com/stac-utils/stac-pydantic
class Link(BaseModel):
    """Link Relation"""

    href: str
    rel: str
    type: Optional[str]
    title: Optional[str]


class MosaicEntity(BaseModel):
    """Dataset Model."""

    id: str # titiler mosaic value
    links: List[Link]
    mosaicjson: MosaicJSON # todo: remove this, maybe?


class StacApiQueryRequestBody(Search):
    """Common request params for MosaicJSON CRUD operations"""

    stac_api_root: str
    asset_name: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    attribution: Optional[str] = None

    # override default Search field for collections, which is List[str]
    collections: Optional[List[str]] = None


class UrisRequestBody(BaseModel):
    # option 2 - a list of files and min/max zoom
    urls: List[str]
    minzoom: Optional[int] = None
    maxzoom: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    attribution: Optional[str] = None
