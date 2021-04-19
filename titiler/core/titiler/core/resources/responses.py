"""Common response models."""

from starlette.responses import JSONResponse, Response


class XMLResponse(Response):
    """XML Response"""

    media_type = "application/xml"


class GeoJSONResponse(JSONResponse):
    """GeoJSON Response"""

    media_type = "application/geo+json"
