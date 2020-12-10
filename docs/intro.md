
`TiTiler` is a python module, which goal is to help user creating dynamic tile server. To learn more about `dynamic tiling` please refer to the [docs](/docs/concepts/dynamic_tiling.md).

User can choose to extend or use `Titiler` as it is.

## Defaults

`TiTiler` comes with a default (complete) application with support of COG, STAC and MosaicJSON. You can start the application locally by doing:

```bash
$ pip install titiler[server]
$ uvicorn titiler.main:app --reload

> INFO: Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
> INFO: Started reloader process [45592]
```

See default endpoints documentation pages:

* [`/cog` - Cloud Optimized GeoTIFF](endpoints/cog.md)
* [`/mosaicjson` - MosaicJSON](endpoints/mosaic.md)
* [`/stac` - Spatio Temporal Asset Catalog](endpoints/stac.md)
* [`/tms` - TileMatrixSets](endpoints/tms.md)

## Customized, minimal app

`TiTiler` has been developed so users can build their own app using only portions they need. Using [`TilerFactory`s](concepts/tiler_factories.md), users can create a fully customized applications with only the endpoints you need.

```python
from titiler.endpoints.factory import TilerFactory
from titiler.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from fastapi import FastAPI

from starlette.requests import Request
from starlette.responses import HTMLResponse

app = FastAPI(
    title="My super app",
    openapi_url="/api/openapi.json",
    description="It's something great",
)

cog = TilerFactory(router_prefix="cog")
app.include_router(cog.router, prefix="/cog", tags=["Cloud Optimized GeoTIFF"])
add_exception_handlers(app, DEFAULT_STATUS_CODES)
```

![](img/custom_app.png)

## Extending TiTiler's app

If you want to include all of Titiler's built-in endpoints, but also include
customized endpoints, you can import and extend the app directly:

```py
from titiler.main import app

from titiler.endpoints.factory import TilerFactory

# Create a custom Tiler (see: https://github.com/developmentseed/titiler-pds/blob/master/app/routes/naip.py)
tiler = TilerFactory(
    router=router,
    prefix="private/cog",
    gdal_config={"AWS_REQUEST_PAYER": "requester"},
)

app.include_router(
    tiler.router,
    prefix="/private/cog",
    tags=["Custom Tiler"]
)
```

More on [customization](/concepts/customization/)
