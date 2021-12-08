"""app

app/main.py

"""

from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from fastapi import FastAPI

from .cache import setup_cache
from .routes import cog

app = FastAPI(title="My simple app with cache")

# Setup Cache on Startup
app.add_event_handler("startup", setup_cache)
add_exception_handlers(app, DEFAULT_STATUS_CODES)

app.include_router(cog.router, tags=["Cloud Optimized GeoTIFF"])
