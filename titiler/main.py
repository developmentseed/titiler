"""titiler app."""

import pkg_resources

from . import settings, version
from .db.memcache import CacheLayer
from .endpoints import cog, mosaic, stac, tms
from .errors import DEFAULT_STATUS_CODES, add_exception_handlers

from fastapi import FastAPI

from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.templating import Jinja2Templates

template_dir = pkg_resources.resource_filename("titiler", "templates")
templates = Jinja2Templates(directory=template_dir)

if settings.MEMCACHE_HOST and not settings.DISABLE_CACHE:
    cache = CacheLayer.create_from_env()
else:
    cache = None


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/v1/openapi.json",
    description="A lightweight Cloud Optimized GeoTIFF tile server",
    version=version,
)

app.include_router(cog.router, prefix="/cog", tags=["Cloud Optimized GeoTIFF"])
app.include_router(stac.router, prefix="/stac", tags=["SpatioTemporal Asset Catalog"])
app.include_router(mosaic.router, prefix="/mosaicjson", tags=["MosaicJSON"])
app.include_router(tms.router)
add_exception_handlers(app, DEFAULT_STATUS_CODES)


# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    origins = [origin.strip() for origin in settings.BACKEND_CORS_ORIGINS.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

app.add_middleware(GZipMiddleware, minimum_size=0)


@app.middleware("http")
async def header_middleware(request: Request, call_next):
    """Add custom header."""
    response = await call_next(request)
    if (
        not response.headers.get("Cache-Control")
        and settings.DEFAULT_CACHECONTROL
        and request.method in ["HEAD", "GET"]
        and response.status_code < 500
    ):
        response.headers["Cache-Control"] = settings.DEFAULT_CACHECONTROL
    return response


@app.middleware("http")
async def cache_middleware(request: Request, call_next):
    """Add cache layer."""
    request.state.cache = cache
    response = await call_next(request)
    if cache:
        request.state.cache.client.disconnect_all()
    return response


@app.get("/ping", description="Health Check", tags=["Health Check"])
def ping():
    """Health check."""
    return {"ping": "pong!"}
