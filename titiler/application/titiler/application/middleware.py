"""Titiler middlewares."""

import logging
import re
import time
from typing import Optional, Set

from fastapi.logger import logger

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp


class CacheControlMiddleware(BaseHTTPMiddleware):
    """MiddleWare to add CacheControl in response headers."""

    def __init__(
        self,
        app: ASGIApp,
        cachecontrol: Optional[str] = None,
        exclude_path: Optional[Set[str]] = None,
    ) -> None:
        """Init Middleware.

        Args:
            app (ASGIApp): starlette/FastAPI application.
            cachecontrol (str): Cache-Control string to add to the response.
            exclude_path (set): Set of regex expression to use to filter the path.

        """
        super().__init__(app)
        self.cachecontrol = cachecontrol
        self.exclude_path = exclude_path or set()

    async def dispatch(self, request: Request, call_next):
        """Add cache-control."""
        response = await call_next(request)
        if self.cachecontrol and not response.headers.get("Cache-Control"):
            for path in self.exclude_path:
                if re.match(path, request.url.path):
                    return response

            if request.method in ["HEAD", "GET"] and response.status_code < 500:
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


class LowerCaseQueryStringMiddleware(BaseHTTPMiddleware):
    """Middleware to make URL parameters case-insensitive.
    taken from: https://github.com/tiangolo/fastapi/issues/826
    """

    async def dispatch(self, request: Request, call_next):
        """dispatch request."""

        self.DECODE_FORMAT = "latin-1"

        query_string = ""
        for k in request.query_params:
            query_string += k.lower() + "=" + request.query_params[k] + "&"

        query_string = query_string[:-1]
        request.scope["query_string"] = query_string.encode(self.DECODE_FORMAT)

        response = await call_next(request)
        return response
