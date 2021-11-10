
**Goal**: add custom TMS to a tiler

**requirements**: titiler.core


1 - Create a custom `TMSParams` dependency

```python
"""dependencies.

app/dependencies.py

"""

from morecantile import tms, TileMatrixSet
from pyproj import CRS

# 1. Create Custom TMS
EPSG6933 = TileMatrixSet.custom(
    (-17357881.81713629, -7324184.56362408, 17357881.81713629, 7324184.56362408),
    CRS.from_epsg(6933),
    identifier="EPSG6933",
    matrix_scale=[1, 1],
)

# 2. Register TMS
tms = tms.register([EPSG6933])

# 3. Create ENUM with available TMS
TileMatrixSetNames = Enum(  # type: ignore
    "TileMatrixSetNames", [(a, a) for a in sorted(tms.list())]
)

# 4. Create Custom TMS dependency
def TMSParams(
    TileMatrixSetId: TileMatrixSetNames = Query(
        TileMatrixSetNames.WebMercatorQuad,  # type: ignore
        description="TileMatrixSet Name (default: 'WebMercatorQuad')",
    )
) -> TileMatrixSet:
    """TileMatrixSet Dependency."""
    return tms.get(TileMatrixSetId.name)
```

2 - Create endpoints

```python
"""routes.

app/routes.py

"""

from titiler.core.factory import TilerFactory, TMSFactory

from .dependencies import TileMatrixSetName, TMSParams


tms = TMSFactory(supported_tms=TileMatrixSetName, tms_dependency=TMSParams)

cog = TilerFactory(tms_dependency=TMSParams)
```

3 - Create app and register our custom endpoints

```python
"""app.

app/main.py

"""

from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from fastapi import FastAPI

from .routes import cog, tms

app = FastAPI(title="My simple app with custom TMS")

app.include_router(cog.router, tags=["Cloud Optimized GeoTIFF"])
app.include_router(tms.router, tags=["TileMatrixSets"])
add_exception_handlers(app, DEFAULT_STATUS_CODES)
```
