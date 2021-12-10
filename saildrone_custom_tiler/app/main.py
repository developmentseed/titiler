"""app

app/main.py

"""

import os
import re

from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from fastapi import FastAPI, HTTPException, Query

from titiler.core.dependencies import DefaultDependency
from titiler.mosaic.factory import MosaicTilerFactory

from .cache import setup_cache
from .routes import cog

MOSAIC_BACKEND = os.getenv("TITILER_MOSAIC_BACKEND", default="")
MOSAIC_HOST = os.getenv("TITILER_MOSAIC_HOST", default="")


def MosaicPathParams(
    mosaic: str = Query(..., description="mosaic name")
) -> str:
    """Create dataset path from args"""
    # mosaic name should be in form of `{user}.{layername}`
    '''
    if not re.match(self.mosaic, r"^[a-zA-Z0-9-_]{1,32}\.[a-zA-Z0-9-_]{1,32}$"):
        raise HTTPException(
            status_code=400,
                detail=f"Invalid mosaic name {self.input}.",
            )
    '''
    #print(f"{MOSAIC_BACKEND}{MOSAIC_HOST}/{mosaic}.json.gz")

    return f"{MOSAIC_BACKEND}{MOSAIC_HOST}{mosaic}.json"



app = FastAPI(title="My simple app with cache")

# Setup Cache on Startup
app.add_event_handler("startup", setup_cache)
add_exception_handlers(app, DEFAULT_STATUS_CODES)

#print(cog.router)
#app.include_router(cog.router, tags=["Cloud Optimized GeoTIFF"])

mosaic = MosaicTilerFactory(path_dependency=MosaicPathParams)
#print(mosaic.router)
app.include_router(mosaic.router, prefix="/mosaic", tags=["Custom backend mosaic"])
