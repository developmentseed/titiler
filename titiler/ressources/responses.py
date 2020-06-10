"""Common response models."""

from starlette.background import BackgroundTask
from starlette.responses import Response


class XMLResponse(Response):
    """XML Response"""

    media_type = "application/xml"


class TileResponse(Response):
    """Tiler's response."""

    def __init__(
        self,
        content: bytes,
        media_type: str,
        status_code: int = 200,
        headers: dict = {},
        background: BackgroundTask = None,
        ttl: int = 3600,
    ) -> None:
        """Init tiler response."""
        headers.update({"Content-Type": media_type})
        if ttl:
            headers.update({"Cache-Control": "max-age=3600"})
        self.body = self.render(content)
        self.status_code = 200
        self.media_type = media_type
        self.background = background
        self.init_headers(headers)
