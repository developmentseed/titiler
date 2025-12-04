
Starting with `titiler>=0.11`, we added a new titiler package `titiler.extensions` which aim to ease the addition of `optional` endpoints to factories.

In `titiler.core.factory.BaseTilerFactory` class, we've added a new attribute: `extensions: List[FactoryExtension] = field(default_factory=list)`. The `list` of extension will then be used in the `post-init` step such as:

```python
def __post_init__(self):
    """Post Init: register route and configure specific options."""
    # Register endpoints
    self.register_routes()

    # Register Extensions
    for ext in self.extensions:
        ext.register(self)

    # Update endpoints dependencies
    for scopes, dependencies in self.route_dependencies:
        self.add_route_dependencies(scopes=scopes, dependencies=dependencies)
```

We defined extension using an *Abstract Base Class* to make sure they implement a `register` method:

```python
@dataclass
class FactoryExtension(metaclass=abc.ABCMeta):
    """Factory Extension."""

    @abc.abstractmethod
    def register(self, factory: "BaseTilerFactory"):
        """Register extension to the factory."""
        ...
```

## Available extensions

#### titiler.extensions.cogValidateExtension

- Goal: adds a `/validate` endpoint which return the content of rio-cogeo `info` method
- Additional requirements: `titiler.extensions["cogeo"]` (installs `rio-cogeo`)

#### titiler.extensions.cogViewerExtension

- Goal: adds a `/viewer` endpoint which return an HTML viewer for simple COGs

#### titiler.extensions.stacViewerExtension

- Goal: adds a `/viewer` endpoint which return an HTML viewer for STAC item

#### titiler.extensions.stacExtension

- Goal: adds a `/stac` endpoint which return an HTML viewer for STAC item
- Additional requirements: `titiler.extensions["stac"]` (installs `rio-stac`)

#### titiler.extensions.wmsExtension

- Goal: adds a `/wms` endpoint to support OGC WMS specification (`GetCapabilities` and `GetMap`)

#### titiler.extensions.wmtsExtension

- Goal: adds a `/WMTSCapabilities.xml` endpoint to support OGC WMTS RESTFULL specification (`GetCapabilities` and `GetTile`)

#### titiler.extensions.stacRenderExtenstion

- Goal: adds `/render` and `/render/{render_id}` endpoints which return the contents of [STAC render extension](https://github.com/stac-extensions/render) and links to tileset.json and WMTS service

#### titiler.xarray.DatasetMetadataExtension

- Goal: adds `/dataset/`, `/dataset/keys` and `/datasets/dict` endpoints which return metadata about a multidimensional Dataset (not a DataArray)

#### titiler.mosaic.extensions.wmts.wmtsExtension

- Goal: adds `/WMTSCapabilities.xml` to support OGC WMTS RESTFULL specification (`GetCapabilities` and `GetTile`)

#### titiler.mosaic.extensions.mosaicjson.MosaicJSONExtension

- Goal: adds `/` and `/validate` endpoints to return MosaicJSON content and validate external mosaics.

## How To

### Use extensions

Extensions must be set at TilerFactory's creation using the `extensions=` options.

```python
from fastapi import FastAPI
from titiler.core.factory import TilerFactory
from titiler.extensions import cogValidateExtension

# Create a FastAPI application
app = FastAPI(description="A lightweight Cloud Optimized GeoTIFF tile server")

# Create a set of endpoints using TiTiler TilerFactory
tiler = TilerFactory(
    router_prefix="/cog",
    extensions=[
        cogValidateExtension()  # the cogeoExtension will add a rio-cogeo /validate endpoint
    ]
)

# Register endpoints to the application
app.include_router(tiler.router, prefix="/cog")
```

### Create your own

```python
from dataclasses import dataclass, field
from typing import Tuple, List, Optional
import rasterio
from starlette.responses import Response
from fastapi import Depends, FastAPI, Query
from titiler.core.factory import TilerFactory, FactoryExtension
from titiler.core.dependencies import ImageRenderingParams
from titiler.core.factory import TilerFactory
from titiler.core.resources.enums import ImageType


@dataclass
class thumbnailExtension(FactoryExtension):
    """Add endpoint to a TilerFactory."""

    # Set some options
    max_size: int = field(default=128)

    # Register method is mandatory and must take a TilerFactory object as input
    def register(self, factory: TilerFactory):
        """Register endpoint to the tiler factory."""

        # register an endpoint to the factory's router
        @factory.router.get(
            "/thumbnail",
            responses={
                200: {
                    "content": {
                        "image/png": {},
                        "image/jpeg": {},
                    },
                    "description": "Return an image.",
                }
            },
            response_class=Response,
        )
        def thumbnail(
            # we can reuse the factory dependency
            src_path: str = Depends(factory.path_dependency),
            reader_params=Depends(factory.reader_dependency),
            layer_params=Depends(factory.layer_dependency),
            dataset_params=Depends(factory.dataset_dependency),
            post_process=Depends(factory.process_dependency),
            colormap=Depends(factory.colormap_dependency),
            render_params=Depends(factory.render_dependency),
            env=Depends(factory.environment_dependency),
        ):
            with rasterio.Env(**env):
                with factory.reader(src_path, **reader_params.as_dict()) as src:
                    image = src.preview(
                        max_size=self.max_size,
                        **layer_params.as_dict(),
                        **dataset_params.as_dict(),
                    )

            if post_process:
                image = post_process(image)

            format = ImageType.jpeg if image.mask.all() else ImageType.png

            if post_process:
                image = post_process(image)

            content, media_type = factory.render_func(
                image,
                colormap=colormap,
                **render_params.as_dict(),
            )

            return Response(content, media_type=media_type)

# Use it
app = FastAPI()
tiler = TilerFactory(
    extensions=[
        thumbnailExtension(max_size=64)
    ]
)
app.include_router(tiler.router)
```
