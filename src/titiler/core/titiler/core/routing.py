"""Custom routing classes."""

from typing import TypedDict

from fastapi import params
from fastapi.dependencies.utils import get_parameterless_sub_dependant
from starlette.routing import BaseRoute, Match


class EndpointScope(TypedDict, total=False):
    """Define endpoint."""

    # More strict version of Starlette's Scope
    # https://github.com/encode/starlette/blob/6af5c515e0a896cbf3f86ee043b88f6c24200bcf/starlette/types.py#L3
    path: str
    method: str
    type: str | None  # http or websocket


def add_route_dependencies(
    routes: list[BaseRoute],
    *,
    scopes: list[EndpointScope],
    dependencies=list[params.Depends],
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
                        depends=depends,
                        path=route.path_format,  # type: ignore
                    ),
                )

            # Register dependencies directly on route so that they aren't ignored if
            # the routes are later associated with an app (e.g. app.include_router(router))
            # https://github.com/tiangolo/fastapi/blob/58ab733f19846b4875c5b79bfb1f4d1cb7f4823f/fastapi/applications.py#L337-L360
            # https://github.com/tiangolo/fastapi/blob/58ab733f19846b4875c5b79bfb1f4d1cb7f4823f/fastapi/routing.py#L677-L678
            route.dependencies.extend(dependencies)  # type: ignore
