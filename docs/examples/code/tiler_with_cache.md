**Goal**: Add a cache layer on top of the tiler

**requirements**: titiler.core, aiocache[redis]

1 - Cache settings

```python
"""settings.

app/settings.py

"""

from pydantic import BaseSettings
from typing import Optional


class CacheSettings(BaseSettings):
    """Cache settings"""

    endpoint: Optional[str] = None
    ttl: int = 3600

    class Config:
        """model config"""

        env_file = ".env"
        env_prefix = "CACHE_"


cache_setting = CacheSettings()
```

2 - Cache plugin

Because `aiocache.cached` doesn't support non-async method we have to create a custom `cached` class

```python
"""Cache Plugin.

app/cache.py

"""

import asyncio
import urllib
from typing import Any, Dict

import aiocache
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from fastapi.dependencies.utils import is_coroutine_callable

from .settings import cache_setting


class cached(aiocache.cached):
    """Custom Cached Decorator."""

    async def get_from_cache(self, key):
        try:
            value = await self.cache.get(key)
            if isinstance(value, Response):
                value.headers["X-Cache"] = "HIT"
            return value
        except Exception:
            aiocache.logger.exception(
                "Couldn't retrieve %s, unexpected error", key
            )

    async def decorator(
        self,
        f,
        *args,
        cache_read=True,
        cache_write=True,
        aiocache_wait_for_write=True,
        **kwargs,
    ):
        key = self.get_cache_key(f, args, kwargs)

        if cache_read:
            value = await self.get_from_cache(key)
            if value is not None:
                return value

        # CUSTOM, we add support for non-async method
        if is_coroutine_callable(f):
            result = await f(*args, **kwargs)
        else:
            result = await run_in_threadpool(f, *args, **kwargs)

        if cache_write:
            if aiocache_wait_for_write:
                await self.set_in_cache(key, result)
            else:
                asyncio.ensure_future(self.set_in_cache(key, result))

        return result


def setup_cache():
    """Setup aiocache."""
    config: Dict[str, Any] = {
        'cache': "aiocache.SimpleMemoryCache",
        'serializer': {
            'class': "aiocache.serializers.PickleSerializer"
        }
    }
    if cache_settings.ttl is not None:
        config["ttl"] = cache_settings.ttl

    if cache_settings.endpoint:
        url = urllib.parse.urlparse(cache_settings.endpoint)
        ulr_config = dict(urllib.parse.parse_qsl(url.query))
        config.update(ulr_config)

        cache_class = aiocache.Cache.get_scheme_class(url.scheme)
        config.update(cache_class.parse_uri_path(url.path))
        config["endpoint"] = url.hostname
        config["port"] = str(url.port)

        if url.password:
            config["password"] = url.password

        if cache_class == aiocache.Cache.REDIS:
            config["cache"] = "aiocache.RedisCache"
        elif cache_class == aiocache.Cache.MEMCACHED:
            config["cache"] = "aiocache.MemcachedCache"

    aiocache.caches.set_config({"default": config})
```

3 - Write a custom minimal Tiler with Cache

```python
"""routes.

app/routes.py
"""
from dataclasses import dataclass
from typing import Callable, Dict, Type
from urllib.parse import urlencode

from fastapi import Depends, Path
from starlette.requests import Request
from starlette.responses import Response

from morecantile import TileMatrixSet
from rio_tiler.io import BaseReader, COGReader

from titiler.core.factory import BaseTilerFactory, img_endpoint_params
from titiler.core.dependencies import ImageParams, MetadataParams, TMSParams
from titiler.core.models.mapbox import TileJSON
from titiler.core.resources.enums import ImageType

from .cache import cached


@dataclass
class TilerFactory(BaseTilerFactory):

    # Default reader is set to COGReader
    reader: Type[BaseReader] = COGReader

    # Endpoint Dependencies
    img_dependency: Type[DefaultDependency] = ImageParams

    # TileMatrixSet dependency
    tms_dependency: Callable[..., TileMatrixSet] = TMSParams

    def register_routes(self):
        """This Method register routes to the router."""
        self.tile()
        self.tilejson()

    def tile(self):
        """Register /tiles endpoint."""

        @self.router.get(r"/tiles/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}", **img_endpoint_params)
        @cached()
        def tile(
            z: int = Path(..., ge=0, le=30, description="TMS tiles's zoom level"),
            x: int = Path(..., description="TMS tiles's column"),
            y: int = Path(..., description="TMS tiles's row"),
            tms: TileMatrixSet = Depends(self.tms_dependency),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            render_params=Depends(self.render_dependency),
            postprocess_params=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
        ):
            """Create map tile from a dataset."""
            with self.reader(src_path, tms=tms) as src_dst:
                data = src_dst.tile(
                    x,
                    y,
                    z,
                    **layer_params,
                    **dataset_params,
                )
                dst_colormap = getattr(src_dst, "colormap", None)

            format = ImageType.jpeg if data.mask.all() else ImageType.png

            image = data.post_process(**postprocess_params)

            content = image.render(
                img_format=format.driver,
                colormap=colormap or dst_colormap,
                **format.profile,
                **render_params,
            )

            return Response(content, media_type=format.mediatype)

    def tilejson(self):
        """Register /tilejson.json endpoint."""

        @self.router.get(
            "/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        @self.router.get(
            "/{TileMatrixSetId}/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        @cached()
        def tilejson(
            request: Request,
            tms: TileMatrixSet = Depends(self.tms_dependency),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            render_params=Depends(self.render_dependency),
            postprocess_params=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
        ):
            """Return TileJSON document for a dataset."""
            route_params = {
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
                "TileMatrixSetId": tms.identifier,
            }
            tiles_url = self.url_for(request, "tile", **route_params)

            qs_key_to_remove = [
                "tilematrixsetid",
                "tile_format",
                "tile_scale",
                "minzoom",
                "maxzoom",
            ]
            qs = [
                (key, value)
                for (key, value) in request.query_params._list
                if key.lower() not in qs_key_to_remove
            ]
            if qs:
                tiles_url += f"?{urlencode(qs)}"

            with self.reader(src_path, tms=tms) as src_dst:
                return {
                    "bounds": src_dst.geographic_bounds,
                    "minzoom": src_dst.minzoom,
                    "maxzoom": src_dst.maxzoom,
                    "name": "cogeotif",
                    "tiles": [tiles_url],
                }


cog = TilerFactory()
```

4 - Create the Tiler app with our custom `DatasetPathParams`

```python
"""app

app/main.py

"""

from titiler.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from fastapi import FastAPI

from .cache import setup_cache
from .routes import cog

app = FastAPI(title="My simple app with cache")

# Setup Cache on Startup
app.add_event_handler("startup", setup_cache)
add_exception_handlers(app, DEFAULT_STATUS_CODES)

app.include_router(cog.router, tags=["Cloud Optimized GeoTIFF"])
```
