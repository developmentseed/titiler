"""Titiler middlewares."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Set
from urllib.parse import urlencode

import structlog
from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from titiler.core import telemetry


@dataclass(frozen=True)
class CacheControlMiddleware:
    """MiddleWare to add CacheControl in response headers.

    Args:
        app (ASGIApp): starlette/FastAPI application.
        cachecontrol (str): Cache-Control string to add to the response.
        exclude_path (set): Set of regex expression to use to filter the path.

    """

    app: ASGIApp
    cachecontrol: str | None = None
    cachecontrol_max_http_code: int = 500
    exclude_path: Set[str] = field(default_factory=set)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """Handle call."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: Message):
            """Send Message."""
            if message["type"] == "http.response.start":
                response_headers = MutableHeaders(scope=message)
                if self.cachecontrol and not response_headers.get("Cache-Control"):
                    if (
                        scope["method"] in ["HEAD", "GET"]
                        and message["status"] < self.cachecontrol_max_http_code
                        and not any(
                            re.match(path, scope["path"]) for path in self.exclude_path
                        )
                    ):
                        response_headers["Cache-Control"] = self.cachecontrol

            await send(message)

        await self.app(scope, receive, send_wrapper)


@dataclass(frozen=True)
class TotalTimeMiddleware:
    """MiddleWare to add Total process time in response headers.

    Args:
        app (ASGIApp): starlette/FastAPI application.

    """

    app: ASGIApp

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """Handle call."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        async def send_wrapper(message: Message):
            """Send Message."""
            nonlocal start_time

            if message["type"] == "http.response.start":
                response_headers = MutableHeaders(scope=message)
                process_time = time.time() - start_time
                app_time = "total;dur={}".format(round(process_time * 1000, 2))

                timings = response_headers.get("Server-Timing")
                response_headers["Server-Timing"] = (
                    f"{timings}, {app_time}" if timings else app_time
                )

            await send(message)

        await self.app(scope, receive, send_wrapper)


@dataclass
class LoggerMiddleware:
    """MiddleWare to add structured logging."""

    app: ASGIApp
    logger: structlog.stdlib.BoundLogger = field(
        default_factory=lambda: structlog.get_logger("titiler.requests")
    )

    def _extract_request_data(self, request: Request) -> dict:
        """Extract and organize request data into nested structure."""
        return {
            "http": {
                "method": request.method,
                "url": str(request.url),
                "scheme": request.url.scheme,
                "host": request.headers.get("host", request.url.hostname or "unknown"),
                "target": request.url.path
                + (f"?{request.url.query}" if request.url.query else ""),
                "user_agent": request.headers.get("user-agent"),
                "referer": next(
                    (request.headers.get(attr) for attr in ["referer", "referrer"]),
                    None,
                ),
                "request": {
                    "headers": {
                        "content_length": request.headers.get("content-length"),
                        "accept_encoding": request.headers.get("accept-encoding"),
                        "origin": request.headers.get("origin"),
                    }
                },
            },
            "net": {
                "host": {
                    "name": request.url.hostname,
                    "port": request.url.port,
                }
            },
            "titiler": {
                "query_params": dict(request.query_params),
            },
        }

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """Handle call."""
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope, receive=receive)
        start_time = time.time()

        request_data = self._extract_request_data(request)

        telemetry_data = self._flatten_for_telemetry(request_data)
        clean_telemetry_data = {
            k: v
            for k, v in telemetry_data.items()
            if v is not None and not isinstance(v, dict)
        }

        for k, v in list(clean_telemetry_data.items()):
            if not isinstance(v, (str, int, float, bool)):
                clean_telemetry_data[k] = str(v)

        telemetry.add_span_attributes(clean_telemetry_data)

        exception: Exception | None = None
        response_started = False

        async def send_wrapper(message: Message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
                request_logger = self.logger.bind(**request_data)
                request_logger.info("Request started")

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            exception = e
        finally:
            duration = time.time() - start_time

            completion_data = {
                "request": {
                    "duration_seconds": duration,
                },
                "titiler": {
                    "path_params": request.path_params,
                },
            }

            if route := scope.get("route"):
                completion_data["http"] = {"route": route.path}

            final_logger = self.logger.bind(**{**request_data, **completion_data})

            if exception:
                final_logger.error(
                    "Request completed with exception",
                    error={
                        "type": type(exception).__name__,
                        "message": str(exception),
                        "occurred": True,
                    },
                    exc_info=True,
                )
            else:
                final_logger.info("Request completed successfully")

        if exception:
            raise exception

    def _flatten_for_telemetry(self, nested_data: dict) -> dict:
        """Flatten nested data for telemetry compatibility."""
        flattened = {}

        def _flatten(obj, prefix=""):
            for key, value in obj.items():
                new_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict) and value:  # Only flatten non-empty dicts
                    _flatten(value, new_key)
                else:
                    flattened[new_key] = value

        _flatten(nested_data)
        return flattened


@dataclass(frozen=True)
class LowerCaseQueryStringMiddleware:
    """Middleware to make URL parameters case-insensitive.
    taken from: https://github.com/tiangolo/fastapi/issues/826

    """

    app: ASGIApp

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """Handle call."""
        if scope["type"] == "http":
            request = Request(scope)
            DECODE_FORMAT = "latin-1"
            query_items = [
                (k.lower(), v) for k, v in request.query_params.multi_items()
            ]
            query_string = urlencode(query_items, doseq=True)
            request.scope["query_string"] = query_string.encode(DECODE_FORMAT)

        await self.app(scope, receive, send)
