"""Custom routing classes."""

import warnings
from typing import Callable, Dict, Optional, Type

import rasterio

from fastapi.routing import APIRoute

from starlette.requests import Request
from starlette.responses import Response


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
        "in titiler 0.1.0. Please see `gdal_config` option in endpoint factories.",
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
