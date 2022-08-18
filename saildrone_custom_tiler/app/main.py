"""app

app/main.py

"""

import os
import re

from titiler.application.custom import templates

from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from titiler.core.dependencies import DefaultDependency
from titiler.mosaic.factory import MosaicTilerFactory

from starlette.requests import Request
from starlette.responses import HTMLResponse

from .cache import setup_cache
#from .routes import sd_cog
from .routes import sd_mosaic
from .routes import sd_s3_proxy

app = FastAPI(title="My simple app with cache")


ENV = os.getenv("SD_ENV", default="production")

# open cors for testing
if "staging" in ENV:
    origins = [
        "http://localhost.saildrone.com",
        "https://localhost.saildrone.com",
        "http://localhost",
        "https://localhost",
        "http://localhost:8080",
        "http://localhost:4000",
        "https://localhost:4000",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Setup Cache on Startup
app.add_event_handler("startup", setup_cache)
add_exception_handlers(app, DEFAULT_STATUS_CODES)

#print(cog.router)
#app.include_router(sd_cog.router, tags=["Cloud Optimized GeoTIFF"])


# mosaic endpoint used for Daily Product png tiles from collection of geotiffs
app.include_router(sd_mosaic.router, prefix="/mosaic", tags=["Custom backend mosaic"])

# s3 proxy endpoint for NRT geotiffs and json lists of desired files
app.include_router(sd_s3_proxy.router, prefix="/nrt", tags=["s3 proxy for NRT"])


@app.get("/healthz", description="Health Check", tags=["Health Check"])
def ping():
    """Health check."""
    return {"ping": "pong!"}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def landing(request: Request):
    """TiTiler Landing page"""
    return templates.TemplateResponse(
        name="index.html",
        context={"request": request},
        media_type="text/html",
    )

@app.get('/status')
def status() -> dict:
    return {
        #'uptime': utils.uptime(),
        'pid': os.getpid()
        # 'dask_cache_size': list(dask_cache.cache.nbytes.keys()),
        #'memory_cache_size': len(backend.cache._cache),
        #'memory_cache_keys': list(backend.cache._cache.keys())
    }
