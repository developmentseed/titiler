"""titiler app."""

from brotli_asgi import BrotliMiddleware

from . import settings, version
from .endpoints import cog, mosaic, stac, tms
from .errors import DEFAULT_STATUS_CODES, add_exception_handlers
from .middleware import CacheControlMiddleware, TotalTimeMiddleware

from fastapi import FastAPI

from starlette.middleware.cors import CORSMiddleware

api_settings = settings.ApiSettings()

app = FastAPI(
    title=api_settings.name,
    description="A lightweight Cloud Optimized GeoTIFF tile server",
    version=version,
)

app.include_router(cog.router, prefix="/cog", tags=["Cloud Optimized GeoTIFF"])
app.include_router(stac.router, prefix="/stac", tags=["SpatioTemporal Asset Catalog"])
app.include_router(mosaic.router, prefix="/mosaicjson", tags=["MosaicJSON"])
app.include_router(tms.router)
add_exception_handlers(app, DEFAULT_STATUS_CODES)


# Set all CORS enabled origins
if api_settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

app.add_middleware(BrotliMiddleware, minimum_size=0, gzip_fallback=True)
app.add_middleware(CacheControlMiddleware, cachecontrol=api_settings.cachecontrol)
app.add_middleware(TotalTimeMiddleware)


@app.get("/ping", description="Health Check", tags=["Health Check"])
def ping():
    """Health check."""
    return {"ping": "pong!"}
