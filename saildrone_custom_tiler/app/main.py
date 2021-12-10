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
from .routes import sd_cog
from .routes import sd_mosaic

app = FastAPI(title="My simple app with cache")

# Setup Cache on Startup
app.add_event_handler("startup", setup_cache)
add_exception_handlers(app, DEFAULT_STATUS_CODES)

#print(cog.router)
#app.include_router(sd_cog.router, tags=["Cloud Optimized GeoTIFF"])

#print(mosaic.router)
app.include_router(sd_mosaic.router, prefix="/mosaic", tags=["Custom backend mosaic"])
