"""Common response models."""

from starlette.responses import Response


class XMLResponse(Response):
    """XML Response"""

    media_type = "application/xml"
