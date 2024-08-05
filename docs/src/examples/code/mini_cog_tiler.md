
**Goal**: Create a simple Raster tiler

**requirements**: titiler.core


```python
"""Minimal COG tiler."""

from titiler.core.factory import TilerFactory
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from fastapi import FastAPI


app = FastAPI(title="My simple app")

cog = TilerFactory()
app.include_router(cog.router, tags=["Cloud Optimized GeoTIFF"])

add_exception_handlers(app, DEFAULT_STATUS_CODES)


@app.get("/healthz", description="Health Check", tags=["Health Check"])
def ping():
    """Health check."""
    return {"ping": "pong!"}
```
