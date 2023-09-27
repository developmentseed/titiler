"""Titiler middlewares."""

import logging
import re
import time
import urllib.parse
from typing import Optional, Set, List, Callable

import jwt
import starlette.status
from fastapi.logger import logger
from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from starlette.responses import JSONResponse


class CacheControlMiddleware:
    """MiddleWare to add CacheControl in response headers."""

    def __init__(
        self,
        app: ASGIApp,
        cachecontrol: Optional[str] = None,
        cachecontrol_max_http_code: Optional[int] = 500,
        exclude_path: Optional[Set[str]] = None,
    ) -> None:
        """Init Middleware.

        Args:
            app (ASGIApp): starlette/FastAPI application.
            cachecontrol (str): Cache-Control string to add to the response.
            exclude_path (set): Set of regex expression to use to filter the path.

        """
        self.app = app
        self.cachecontrol = cachecontrol
        self.cachecontrol_max_http_code = cachecontrol_max_http_code
        self.exclude_path = exclude_path or set()

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
                            [
                                re.match(path, scope["path"])
                                for path in self.exclude_path
                            ]
                        )
                    ):
                        response_headers["Cache-Control"] = self.cachecontrol

            await send(message)

        await self.app(scope, receive, send_wrapper)


class TotalTimeMiddleware:
    """MiddleWare to add Total process time in response headers."""

    def __init__(self, app: ASGIApp) -> None:
        """Init Middleware.

        Args:
            app (ASGIApp): starlette/FastAPI application.

        """
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """Handle call."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        async def send_wrapper(message: Message):
            """Send Message."""
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


class LoggerMiddleware:
    """MiddleWare to add logging."""

    def __init__(
        self,
        app: ASGIApp,
        querystrings: bool = False,
        headers: bool = False,
    ) -> None:
        """Init Middleware.

        Args:
            app (ASGIApp): starlette/FastAPI application.

        """
        self.app = app
        self.querystrings = querystrings
        self.headers = headers
        self.logger = logger
        logger.setLevel(logging.DEBUG)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """Handle call."""
        if scope["type"] == "http":
            request = Request(scope)

            self.logger.debug(str(request.url))

            qs = dict(request.query_params)
            if qs and self.querystrings:
                self.logger.debug(qs)

            if self.headers:
                self.logger.debug(dict(request.headers))

        await self.app(scope, receive, send)


class LowerCaseQueryStringMiddleware:
    """Middleware to make URL parameters case-insensitive.
    taken from: https://github.com/tiangolo/fastapi/issues/826
    """

    def __init__(self, app: ASGIApp) -> None:
        """Init Middleware.

        Args:
            app (ASGIApp): starlette/FastAPI application.

        """
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """Handle call."""
        if scope["type"] == "http":
            request = Request(scope)

            DECODE_FORMAT = "latin-1"

            query_string = ""
            for k, v in request.query_params.multi_items():
                query_string += k.lower() + "=" + urllib.parse.quote(v) + "&"

            query_string = query_string[:-1]
            request.scope["query_string"] = query_string.encode(DECODE_FORMAT)

        await self.app(scope, receive, send)


class FakeHttpsMiddleware:
    """Middleware to make http request to fake https request"""

    def __init__(self, app: ASGIApp) -> None:
        """Init Middleware.

        Args:
            app (ASGIApp): starlette/FastAPI application.

        """
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """Handle call."""
        if scope["type"] == "http" and scope["scheme"] == "http":
            scope["scheme"] = "https"

        await self.app(scope, receive, send)


class JWTAuthenticationMiddleware:
    """Middleware to authentication with jwt"""

    def __init__(self, app: ASGIApp, secret: str, user_key="user", algorithms: List[str]=None) -> None:
        """Init Middleware.

        Args:
            app (ASGIApp): starlette/FastAPI application.
            secret (str): jwt secret for authentication
            user_key (str): key of jwt payload to get user
            algorithms (List[str]): algorithms for decode jwt. default ["HS512"]
        """
        if algorithms is None:
            algorithms = ["HS512"]
        from fastapi.security import HTTPBearer
        self.app = app
        self.secret = secret
        self.http_bearer = HTTPBearer(bearerFormat="jwt", auto_error=False)
        self.algorithms = algorithms
        self.user_key = user_key

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        async def response401(message: str="Not authenticated"):
            response = JSONResponse(content={"detail": message},
                                    status_code=starlette.status.HTTP_401_UNAUTHORIZED)
            await response(scope, receive, send)
        """Handle call."""
        if scope["type"] == "http":
            request = Request(scope)
            credentials = await self.http_bearer(request)
            if not credentials:
                await response401("access token is required")
                return
            try:
                payload = jwt.decode(credentials.credentials, self.secret, algorithms=self.algorithms)
            except jwt.DecodeError as e:
                await response401("unsupported token")
            except jwt.InvalidTokenError as e:
                await response401("invalid token")
                return
            user = payload[self.user_key]
            scope['auth'] = credentials.credentials
            scope['user'] = user

        await self.app(scope, receive, send)
