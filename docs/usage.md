# Default App

TiTiler comes with a default (complete) application with support of COG, STAC and MosaicJSON. You can start the application locally by doing:

```bash
$ pip install titiler[server]
$ uvicorn titiler.main:app --reload

> INFO: Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
> INFO: Started reloader process [45592]
```

Default endpoints documentation:

* [`/cog` - Cloud Optimized GeoTIFF](endpoints/cog.md)
* [`/mosaicjson` - MosaicJSON](endpoints/mosaic.md)
* [`/stac` - Spatio Temporal Asset Catalog](endpoints/stac.md)
* [`/tms` - TileMatrixSets](endpoints/tms.md)

# Create your own App

TiTiler has been developed so users can build their own app using only portions they need. Using [`TilerFactory`s](concepts/tiler_factories.md), you can create customized applications with only the endpoints you need.

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
