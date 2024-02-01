
**Goal**: add custom TMS to a tiler

**requirements**: titiler.core

1 - Create custom TMS and custom endpoints

```python
"""routes.

app/routes.py

"""

from titiler.core.factory import TilerFactory, TMSFactory
from morecantile import tms, TileMatrixSet
from pyproj import CRS

# 1. Create Custom TMS
EPSG6933 = TileMatrixSet.custom(
    (-17357881.81713629, -7324184.56362408, 17357881.81713629, 7324184.56362408),
    CRS.from_epsg(6933),
    id="EPSG6933",
    matrix_scale=[1, 1],
)
# 2. Register TMS
tms = tms.register({EPSG6933.id:EPSG6933})

tms_factory = TMSFactory(supported_tms=tms)
cog_factory = TilerFactory(supported_tms=tms)
```

2 - Create app and register our custom endpoints

```python
"""app.

app/main.py

"""

from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from fastapi import FastAPI

from .routes import cog_factory, tms_factory

app = FastAPI(title="My simple app with custom TMS")

app.include_router(cog_factory.router, tags=["Cloud Optimized GeoTIFF"])
app.include_router(tms_factory.router, tags=["Tiling Schemes"])
add_exception_handlers(app, DEFAULT_STATUS_CODES)
```
