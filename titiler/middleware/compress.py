from brotli import MODE_FONT, MODE_GENERIC, MODE_TEXT  # type: ignore
from brotli_middleware import BrotliResponder

from starlette.datastructures import Headers, MutableHeaders
from starlette.middleware.gzip import GZipResponder
from starlette.types import ASGIApp, Receive, Scope, Send


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
