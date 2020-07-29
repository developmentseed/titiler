"""Common response models."""

from starlette.responses import JSONResponse as JSONResponseBase
from starlette.responses import Response


class XMLResponse(Response):
    """XML Response"""

    media_type = "application/xml"


class ImgResponse(Response):
    """Image response."""

    def __init__(self, *args, ttl: int = 2600, **kwargs):
        """Create response with cache header"""
        super().__init__(*args, **kwargs)
        self.headers.update({"Cache-Control": f"max-age={ttl}"})


class JSONResponse(JSONResponseBase):
    """JSON response."""

    def __init__(self, *args, ttl: int = 3600, **kwargs):
        """Create response with cache header"""
        super().__init__(*args, **kwargs)
        self.headers.update({"Cache-Control": f"max-age={ttl}"})
