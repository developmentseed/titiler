"""Titiler middlewares."""

import time
from typing import Optional

from brotli import MODE_FONT, MODE_GENERIC, MODE_TEXT  # type: ignore
from brotli_middleware import BrotliResponder

from starlette.datastructures import Headers
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipResponder
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send


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

class BrotliMode:
    """Brotli available modes."""

    generic = MODE_GENERIC
    text = MODE_TEXT
    font = MODE_FONT


class CompressMiddleware:
    """Brotli middleware public interface."""

    def __init__(
        self,
        app: ASGIApp,
        quality: int = 4,
        mode: str = "text",
        lgwin: int = 22,
        lgblock: int = 0,
        minimum_size: int = 400,
    ) -> None:
        """
        Arguments.
        mode: The compression mode can be:
            generic (default), text (for UTF-8 format text input)
            or font (for WOFF 2.0).
        quality: Controls the compression-speed vs compression-
            density tradeoff. The higher the quality, the slower the compression.
            Range is 0 to 11.
        lgwin: Base 2 logarithm of the sliding window size. Range
            is 10 to 24.
        lgblock: Base 2 logarithm of the maximum input block size.
            Range is 16 to 24. If set to 0, the value will be set based on the
            quality.
        minimum_size: Only compress responses that are bigger than this value in bytes.
        """
        self.app = app
        self.quality = quality
        self.mode = getattr(BrotliMode, mode)
        self.minimum_size = minimum_size
        self.lgwin = lgwin
        self.lgblock = lgblock

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = Headers(scope=scope)
            if "br" in headers.get("Accept-Encoding", ""):
                responder = BrotliResponder(
                    self.app,
                    self.quality,
                    self.mode,
                    self.lgwin,
                    self.lgblock,
                    self.minimum_size,
                )
                await responder(scope, receive, send)
                return

            if "gzip" in headers.get("Accept-Encoding", ""):
                responder = GZipResponder(self.app, self.minimum_size)
                await responder(scope, receive, send)
                return

        await self.app(scope, receive, send)
