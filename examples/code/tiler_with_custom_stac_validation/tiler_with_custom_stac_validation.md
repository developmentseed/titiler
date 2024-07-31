
**Goal**: Create a custom STAC endpoints with validation

**requirements**: `titiler.core` && `jsonschema`


```python
"""FastAPI application."""

from fastapi import FastAPI

from rio_tiler.io import STACReader

from titiler.core.dependencies import DatasetPathParams
from titiler.core.factory import MultiBaseTilerFactory
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers


# STAC uses MultiBaseReader so we use MultiBaseTilerFactory to built the default endpoints
stac = MultiBaseTilerFactory(reader=STACReader, router_prefix="stac")


# We add `/validate` to the router
@stac.router.get("/validate")
def stac_validate_get(src_path=Depends(DatasetPathParams)):
    """STAC validation."""
    with STACReader(src_path) as stac_src:
       return stac_src.item.validate()


# Create FastAPI application
app = FastAPI(title="My simple app with custom STAC endpoint")
app.include_router(stac.router, tags=["STAC"])
add_exception_handlers(app, DEFAULT_STATUS_CODES)
```
