"""Microsoft Azure Function."""

import azure.functions as func
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette_cramjam.middleware import CompressionMiddleware

from titiler.application import __version__ as titiler_version
from titiler.application.main import cog, mosaic, stac, templates, tms
from titiler.application.settings import ApiSettings
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.middleware import (
    CacheControlMiddleware,
    LoggerMiddleware,
    LowerCaseQueryStringMiddleware,
    TotalTimeMiddleware,
)
from titiler.mosaic.errors import MOSAIC_STATUS_CODES

api_settings = ApiSettings()

app = FastAPI(
    title=api_settings.name,
    description="A lightweight Cloud Optimized GeoTIFF tile server",
    version=titiler_version,
    root_path=api_settings.root_path,
)

if not api_settings.disable_cog:
    app.include_router(cog.router, prefix="/cog", tags=["Cloud Optimized GeoTIFF"])

if not api_settings.disable_stac:
    app.include_router(
        stac.router, prefix="/stac", tags=["SpatioTemporal Asset Catalog"]
    )

if not api_settings.disable_mosaic:
    app.include_router(mosaic.router, prefix="/mosaicjson", tags=["MosaicJSON"])

app.include_router(tms.router, tags=["TileMatrixSets"])
add_exception_handlers(app, DEFAULT_STATUS_CODES)
add_exception_handlers(app, MOSAIC_STATUS_CODES)


# Set all CORS enabled origins
if api_settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

app.add_middleware(
    CompressionMiddleware,
    minimum_size=0,
    exclude_mediatype={
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/jp2",
        "image/webp",
    },
)

app.add_middleware(
    CacheControlMiddleware,
    cachecontrol=api_settings.cachecontrol,
    exclude_path={r"/healthz"},
)

if api_settings.debug:
    app.add_middleware(LoggerMiddleware, headers=True, querystrings=True)
    app.add_middleware(TotalTimeMiddleware)

if api_settings.lower_case_query_parameters:
    app.add_middleware(LowerCaseQueryStringMiddleware)


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


async def main(
    req: func.HttpRequest,
    context: func.Context,
) -> func.HttpResponse:
    """Run App in AsgiMiddleware."""
    return await func.AsgiMiddleware(app).handle_async(req, context)
