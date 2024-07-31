**Goal**: Add a cache layer on top of the tiler

**requirements**: titiler.core, aiocache[redis]

Note: Use aioredis 1.3 because aiocache [doesnt work](https://github.com/aio-libs/aiocache/issues/543) with aioredis version [2.0](https://github.com/aio-libs/aioredis-py/releases/tag/v2.0.0)

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
    namespace: str = ""

    class Config:
        """model config"""

        env_file = ".env"
        env_prefix = "CACHE_"


cache_setting = CacheSettings()
```

Env file example with redis URI

```
CACHE_ENDPOINT=redis://127.0.0.1:6379/0
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
    if cache_setting.ttl is not None:
        config["ttl"] = cache_setting.ttl

    if cache_setting.endpoint:
        url = urllib.parse.urlparse(cache_setting.endpoint)
        ulr_config = dict(urllib.parse.parse_qsl(url.query))
        config.update(ulr_config)

        cache_class = aiocache.Cache.get_scheme_class(url.scheme)
        config.update(cache_class.parse_uri_path(url.path))
        config["endpoint"] = url.hostname
        config["port"] = str(url.port)

        # Add other configuration into config here, Example for namespace:
        """
        if cache_setting.namespace != "":
            config["namespace"] = cache_setting.namespace
        """

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
from typing import Callable, Dict, Type, Literal, List, Tuple, Optional
from urllib.parse import urlencode

from fastapi import Depends, Path, Query
from starlette.requests import Request
from starlette.responses import Response

from morecantile import TileMatrixSet
from rio_tiler.io import BaseReader, Reader

from titiler.core.factory import img_endpoint_params
from titiler.core.factory import TilerFactory as TiTilerFactory
from titiler.core.dependencies import RescalingParams
from titiler.core.models.mapbox import TileJSON
from titiler.core.resources.enums import ImageType

from .cache import cached


@dataclass
class TilerFactory(TiTilerFactory):

    reader: Type[BaseReader] = Reader

    def register_routes(self):
        """This Method register routes to the router."""

        @self.router.get(r"/tiles/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}.{format}", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}@{scale}x", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}@{scale}x.{format}", **img_endpoint_params)
        @self.router.get(r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(
            r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}.{format}", **img_endpoint_params
        )
        @self.router.get(
            r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x", **img_endpoint_params
        )
        @self.router.get(
            r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
            **img_endpoint_params,
        )
        # Add default cache config dictionary into cached alias.
        # Note: if alias is used, other arguments in cached will be ignored. Add other arguments into default dicttionary in setup_cache function.
        @cached(alias="default")
        def tile(
            z: int = Path(..., ge=0, le=30, description="TMS tiles's zoom level"),
            x: int = Path(..., description="TMS tiles's column"),
            y: int = Path(..., description="TMS tiles's row"),
            tileMatrixSetId: Literal[tuple(self.supported_tms.list())] = Query(
                self.default_tms,
                description=f"TileMatrixSet Name (default: '{self.default_tms}')",
            ),
            scale: int = Query(
                1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
            ),
            format: ImageType = Query(
                None, description="Output image type. Default is auto."
            ),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            buffer: Optional[float] = Query(
                None,
                gt=0,
                title="Tile buffer.",
                description="Buffer on each side of the given tile. It must be a multiple of `0.5`. Output **tilesize** will be expanded to `tilesize + 2 * buffer` (e.g 0.5 = 257x257, 1.0 = 258x258).",
            ),
            post_process=Depends(self.process_dependency),
            rescale: Optional[List[Tuple[float, ...]]] = Depends(RescalingParams),
            color_formula: Optional[str] = Query(
                None,
                title="Color Formula",
                description="rio-color formula (info: https://github.com/mapbox/rio-color)",
            ),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            reader_params=Depends(self.reader_dependency),
        ):
            """Create map tile from a dataset."""
            tms = self.supported_tms.get(tileMatrixSetId)

            with self.reader(src_path, tms=tms, **reader_params) as src_dst:
                image = src_dst.tile(
                    x,
                    y,
                    z,
                    tilesize=scale * 256,
                    buffer=buffer,
                    **layer_params,
                    **dataset_params,
                )
                dst_colormap = getattr(src_dst, "colormap", None)


            if post_process:
                image = post_process(image)

            if rescale:
                image.rescale(rescale)

            if color_formula:
                image.apply_color_formula(color_formula)

            if cmap := colormap or dst_colormap:
                image = image.apply_colormap(cmap)

            if not format:
                format = ImageType.jpeg if image.mask.all() else ImageType.png

            content = image.render(
                img_format=format.driver,
                **format.profile,
                **render_params,
            )

            return Response(content, media_type=format.mediatype)

        @self.router.get(
            "/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        @self.router.get(
            "/{tileMatrixSetId}/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        @cached(alias="default")
        def tilejson(
            request: Request,
            tileMatrixSetId: Literal[tuple(self.supported_tms.list())] = Query(
                self.default_tms,
                description=f"TileMatrixSet Name (default: '{self.default_tms}')",
            ),
            src_path=Depends(self.path_dependency),
            tile_format: Optional[ImageType] = Query(
                None, description="Output image type. Default is auto."
            ),
            tile_scale: int = Query(
                1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
            ),
            minzoom: Optional[int] = Query(
                None, description="Overwrite default minzoom."
            ),
            maxzoom: Optional[int] = Query(
                None, description="Overwrite default maxzoom."
            ),
            layer_params=Depends(self.layer_dependency),  # noqa
            dataset_params=Depends(self.dataset_dependency),  # noqa
            buffer: Optional[float] = Query(  # noqa
                None,
                gt=0,
                title="Tile buffer.",
                description="Buffer on each side of the given tile. It must be a multiple of `0.5`. Output **tilesize** will be expanded to `tilesize + 2 * buffer` (e.g 0.5 = 257x257, 1.0 = 258x258).",
            ),
            post_process=Depends(self.process_dependency),  # noqa
            rescale: Optional[List[Tuple[float, ...]]] = Depends(
                RescalingParams
            ),  # noqa
            color_formula: Optional[str] = Query(  # noqa
                None,
                title="Color Formula",
                description="rio-color formula (info: https://github.com/mapbox/rio-color)",
            ),
            colormap=Depends(self.colormap_dependency),  # noqa
            render_params=Depends(self.render_dependency),  # noqa
            reader_params=Depends(self.reader_dependency),
        ):
            """Return TileJSON document for a dataset."""
            route_params = {
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
                "scale": tile_scale,
                "tileMatrixSetId": tileMatrixSetId,
            }
            if tile_format:
                route_params["format"] = tile_format.value

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

            tms = self.supported_tms.get(tileMatrixSetId)
            with self.reader(src_path, tms=tms, **reader_params) as src_dst:
                return {
                    "bounds": src_dst.geographic_bounds,
                    "minzoom": minzoom if minzoom is not None else src_dst.minzoom,
                    "maxzoom": maxzoom if maxzoom is not None else src_dst.maxzoom,
                    "tiles": [tiles_url],
                }

        # Register Map viewer
        self.map_viewer()

cog = TilerFactory()
```

4 - Create the Tiler app with our custom `DatasetPathParams`

```python
"""app

app/main.py

"""

from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from fastapi import FastAPI

from .cache import setup_cache
from .routes import cog

app = FastAPI(title="My simple app with cache")

# Setup Cache on Startup
app.add_event_handler("startup", setup_cache)
add_exception_handlers(app, DEFAULT_STATUS_CODES)

app.include_router(cog.router, tags=["Cloud Optimized GeoTIFF"])
```
