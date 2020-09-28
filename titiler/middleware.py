"""Titiler middlewares."""

import time
from typing import Optional

from brotli import MODE_GENERIC  # type: ignore
from brotli_middleware import BrotliResponder

from starlette.datastructures import Headers
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipResponder
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

DEFAULT_BROTLI_CONFIG = {
    "quality": 4,
    "mode": MODE_GENERIC,
    "lgwin": 22,
    "lgblock": 0,
}


class CacheControlMiddleware(BaseHTTPMiddleware):
    """MiddleWare to add CacheControl in response headers."""

    def __init__(self, app: ASGIApp, cachecontrol: Optional[str] = None) -> None:
        """Init Middleware."""
        super().__init__(app)
        self.cachecontrol = cachecontrol

    async def dispatch(self, request: Request, call_next):
        """Add cache-control."""
        response = await call_next(request)
        if (
            not response.headers.get("Cache-Control")
            and self.cachecontrol
            and request.method in ["HEAD", "GET"]
            and response.status_code < 500
        ):
            response.headers["Cache-Control"] = self.cachecontrol
        return response


class TotalTimeMiddleware(BaseHTTPMiddleware):
    """MiddleWare to add Total process time in response headers."""

    async def dispatch(self, request: Request, call_next):
        """Add X-Process-Time."""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        timings = response.headers.get("Server-Timing")
        app_time = "total;dur={}".format(round(process_time * 1000, 2))
        response.headers["Server-Timing"] = (
            f"{timings}, {app_time}" if timings else app_time
        )
        return response


class CompressMiddleware:
    """Brotli middleware public interface."""

    def __init__(self, app: ASGIApp, minimum_size: int = 400, **kwargs) -> None:
        """
        Arguments.
        minimum_size: Only compress responses that are bigger than this value in bytes. Used for both brotli and gzip compression.

        kwargs: arguments to be passed on to brotli encoder
            mode: The compression mode can be:
                brotli.MODE_GENERIC (default), brotli.MODE_TEXT (for UTF-8
                format text input) or brotli.MODE_FONT (for WOFF 2.0).
            quality: Controls the compression-speed vs compression-
                density tradeoff. The higher the quality, the slower the compression.
                Range is 0 to 11.
            lgwin: Base 2 logarithm of the sliding window size. Range
                is 10 to 24.
            lgblock: Base 2 logarithm of the maximum input block size.
                Range is 16 to 24. If set to 0, the value will be set based on the
                quality.
        """
        self.app = app
        self.minimum_size = minimum_size
        self.brotli_kwargs = {**DEFAULT_BROTLI_CONFIG, **kwargs}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Select Brotli or Gzip responders as needed
        """
        if scope["type"] == "http":
            headers = Headers(scope=scope)
            if "br" in headers.get("Accept-Encoding", ""):
                responder = BrotliResponder(
                    self.app, minimum_size=self.minimum_size, **self.brotli_kwargs
                )
                await responder(scope, receive, send)
                return

            if "gzip" in headers.get("Accept-Encoding", ""):
                responder = GZipResponder(self.app, self.minimum_size)
                await responder(scope, receive, send)
                return

        await self.app(scope, receive, send)
