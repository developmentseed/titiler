"""titiler app."""
import importlib

from titiler import settings, version
from titiler.db.memcache import CacheLayer
from titiler.endpoints import cog, demo, stac, tms
from titiler.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from fastapi import FastAPI

from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request

if settings.MEMCACHE_HOST and not settings.DISABLE_CACHE:
    cache = CacheLayer.create_from_env()
else:
    cache = None


def _include_extra_router(app: FastAPI, module: str, **kwargs) -> None:
    """Helper function to add routers available through pip extras"""
    try:
        mod = importlib.import_module(module)
        app.include_router(mod.router, **kwargs)  # type: ignore
    except ModuleNotFoundError:
        pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/v1/openapi.json",
    description="A lightweight Cloud Optimized GeoTIFF tile server",
    version=version,
)
app.include_router(cog.router, prefix="/cog", tags=["Cloud Optimized GeoTIFF"])
app.include_router(stac.router, prefix="/stac", tags=["SpatioTemporal Asset Catalog"])
_include_extra_router(
    app, module="titiler.endpoints.mosaic", prefix="/mosaicjson", tags=["MosaicJSON"]
)
app.include_router(tms.router)
app.include_router(demo.router)

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
