"""Titiler.mosaic Models."""

from cogeo_mosaic.mosaic import MosaicJSON
from typing import List, Optional

from stac_pydantic.api import Search
from pydantic import BaseModel, validator

import re

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


rfc3339_regex_str = r"^(\d\d\d\d)\-(\d\d)\-(\d\d)(T|t)" \
                    r"(\d\d):(\d\d):(\d\d)(\.\d+)?(Z|([-+])(\d\d):(\d\d))$"
rfc3339_regex = re.compile(rfc3339_regex_str)

class StacApiQueryRequestBody(Search):
    """Common request params for MosaicJSON CRUD operations"""

    stac_api_root: str
    asset_name: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    attribution: Optional[str] = None
    version: Optional[str] = None

    # override default Search field for collections, which is List[str]
    collections: Optional[List[str]] = None
    # overriding limit so we can tell if it's defined or not
    limit: Optional[int]

    # copied from Search to fix https://github.com/stac-utils/stac-pydantic/issues/78
    # override
    @validator("datetime")
    def validate_datetime(cls, v):
        if "/" in v:
            values = v.split("/")
        else:
            # Single date is interpreted as end date
            values = ["..", v]

        dates = []
        for value in values:
            if value == "..":
                dates.append(value)
                continue
            if not rfc3339_regex.match(value):
                raise ValueError(
                    f"Invalid datetime, must match format ({rfc3339_regex_str})."
                )
            dates.append(value)

        # this should get validated by the server anyway
        # if ".." not in dates:
        #     if datetime.strptime(dates[0], DATETIME_RFC339) > datetime.strptime(
        #         dates[1], DATETIME_RFC339
        #     ):
        #         raise ValueError(
        #             "Invalid datetime range, must match format (begin_date, end_date)"
        #         )
        return v

class UrisRequestBody(BaseModel):
    # option 2 - a list of files and min/max zoom
    urls: List[str]
    minzoom: Optional[int] = None
    maxzoom: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    attribution: Optional[str] = None
    version: Optional[str] = None


class TooManyResultsException(Exception):
    def __init__(self, message):
        self.message = message


class StoreException(Exception):
    def __init__(self, message):
        self.message = message
