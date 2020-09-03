"""titiler app."""

from . import settings, version
from .endpoints import cog, mosaic, stac, tms
from .errors import DEFAULT_STATUS_CODES, add_exception_handlers

from fastapi import FastAPI

from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request

api_settings = settings.ApiSettings()

app = FastAPI(
    title=api_settings.name,
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
if api_settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.cors_origins,
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
        and api_settings.cachecontrol
        and request.method in ["HEAD", "GET"]
        and response.status_code < 500
    ):
        response.headers["Cache-Control"] = api_settings.cachecontrol
    return response


@app.get("/ping", description="Health Check", tags=["Health Check"])
def ping():
    """Health check."""
    return {"ping": "pong!"}
