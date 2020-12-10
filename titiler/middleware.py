"""Titiler middlewares."""

import logging
import time
from typing import Optional

from fastapi.logger import logger

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp


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


class LoggerMiddleware(BaseHTTPMiddleware):
    """MiddleWare to add logging."""

    def __init__(
        self, app: ASGIApp, querystrings: bool = False, headers: bool = False,
    ) -> None:
        """Init Middleware."""
        super().__init__(app)
        self.logger = logger
        logger.setLevel(logging.DEBUG)

        self.querystrings = querystrings
        self.headers = headers

    async def dispatch(self, request: Request, call_next):
        """Add logs."""
        self.logger.debug(str(request.url))
        qs = dict(request.query_params)
        if qs and self.querystrings:
            self.logger.debug(qs)
        if self.headers:
            self.logger.debug(dict(request.headers))

        response = await call_next(request)
        return response
