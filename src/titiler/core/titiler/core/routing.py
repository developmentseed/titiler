"""Custom routing classes."""

import warnings
from typing import Callable, Dict, List, Optional, Type

import rasterio
from fastapi import params
from fastapi.dependencies.utils import get_parameterless_sub_dependant
from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Match
from typing_extensions import TypedDict


def apiroute_factory(env: Optional[Dict] = None) -> Type[APIRoute]:
    """
    Create Custom API Route class with custom Env.

    Because we cannot create middleware for specific router we need to create
    a custom APIRoute which add the `rasterio.Env(` block before the endpoint is
    actually called. This way we set the env outside the threads and we make sure
    that event multithreaded Reader will get the environment set.

    Note: This has been tested in python 3.6 and 3.7 only.

    """
    warnings.warn(
        "'apiroute_factory' has been deprecated and will be removed"
        "in titiler 0.1.0. Please see `environment_dependency` option in endpoint factories.",
        DeprecationWarning,
    )

    class EnvAPIRoute(APIRoute):
        """Custom API route with env."""

        config = env or {}

        def get_route_handler(self) -> Callable:
            original_route_handler = super().get_route_handler()

            async def custom_route_handler(request: Request) -> Response:
                with rasterio.Env(**self.config):
                    response: Response = await original_route_handler(request)
                return response

            return custom_route_handler

    return EnvAPIRoute


class EndpointScope(TypedDict, total=False):
    """Define endpoint."""

    # More strict version of Starlette's Scope
    # https://github.com/encode/starlette/blob/6af5c515e0a896cbf3f86ee043b88f6c24200bcf/starlette/types.py#L3
    path: str
    method: str
    type: Optional[str]  # http or websocket


def add_route_dependencies(
    routes: List[BaseRoute],
    *,
    scopes: List[EndpointScope],
    dependencies=List[params.Depends],
):
    """Add dependencies to routes.

    Allows a developer to add dependencies to a route after the route has been defined.

    """
    for route in routes:
        for scope in scopes:
            match, _ = route.matches({"type": "http", **scope})  # type: ignore
            if match != Match.FULL:
                continue

            # Mimicking how APIRoute handles dependencies:
            # https://github.com/tiangolo/fastapi/blob/1760da0efa55585c19835d81afa8ca386036c325/fastapi/routing.py#L408-L412
            for depends in dependencies[::-1]:
                route.dependant.dependencies.insert(  # type: ignore
                    0,
                    get_parameterless_sub_dependant(
                        depends=depends, path=route.path_format  # type: ignore
                    ),
                )

            # Register dependencies directly on route so that they aren't ignored if
            # the routes are later associated with an app (e.g. app.include_router(router))
            # https://github.com/tiangolo/fastapi/blob/58ab733f19846b4875c5b79bfb1f4d1cb7f4823f/fastapi/applications.py#L337-L360
            # https://github.com/tiangolo/fastapi/blob/58ab733f19846b4875c5b79bfb1f4d1cb7f4823f/fastapi/routing.py#L677-L678
            route.dependencies.extend(dependencies)  # type: ignore
