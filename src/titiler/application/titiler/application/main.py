"""titiler app."""

import logging

from rio_cogeo.cogeo import cog_info as rio_cogeo_info
from rio_cogeo.models import Info
from rio_tiler.io import COGReader, STACReader

from titiler.application import __version__ as titiler_version
from titiler.application.settings import ApiSettings
from titiler.core.dependencies import DatasetPathParams
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.factory import MultiBaseTilerFactory, TilerFactory, TMSFactory
from titiler.core.middleware import (
    CacheControlMiddleware,
    LoggerMiddleware,
    LowerCaseQueryStringMiddleware,
    TotalTimeMiddleware,
)
from titiler.mosaic.errors import MOSAIC_STATUS_CODES
from titiler.mosaic.factory import MosaicTilerFactory

from fastapi import Depends, FastAPI, Query

from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from starlette_cramjam.middleware import CompressionMiddleware

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore

logging.getLogger("botocore.credentials").disabled = True
logging.getLogger("botocore.utils").disabled = True
logging.getLogger("rio-tiler").setLevel(logging.ERROR)

# TODO: mypy fails in python 3.9, we need to find a proper way to do this
templates = Jinja2Templates(directory=str(resources_files(__package__) / "templates"))  # type: ignore

api_settings = ApiSettings()

app = FastAPI(
    title=api_settings.name,
    description="A lightweight Cloud Optimized GeoTIFF tile server",
    version=titiler_version,
    root_path=api_settings.root_path,
)

###############################################################################
# Simple Dataset endpoints (e.g Cloud Optimized GeoTIFF)
if not api_settings.disable_cog:
    cog = TilerFactory(reader=COGReader, router_prefix="/cog")

    # Add validate and viewer endpoints
    @cog.router.get("/validate", response_model=Info)
    def validate(
        src_path: str = Depends(DatasetPathParams),
        strict: bool = Query(False, description="Treat warnings as errors"),
    ):
        """Validate a COG"""
        return rio_cogeo_info(src_path, strict=strict)

    @cog.router.get("/viewer", response_class=HTMLResponse)
    def cog_viewer(request: Request):
        """COG Viewer."""
        return templates.TemplateResponse(
            name="cog_index.html",
            context={
                "request": request,
                "tilejson_endpoint": cog.url_for(request, "tilejson"),
                "info_endpoint": cog.url_for(request, "info"),
                "statistics_endpoint": cog.url_for(request, "statistics"),
            },
            media_type="text/html",
        )

    app.include_router(cog.router, prefix="/cog", tags=["Cloud Optimized GeoTIFF"])


###############################################################################
# STAC endpoints
if not api_settings.disable_stac:
    stac = MultiBaseTilerFactory(reader=STACReader, router_prefix="/stac")

    # Add viewer endpoint
    @stac.router.get("/viewer", response_class=HTMLResponse)
    def stac_viewer(request: Request):
        """STAC Viewer."""
        return templates.TemplateResponse(
            name="stac_index.html",
            context={
                "request": request,
                "tilejson_endpoint": stac.url_for(request, "tilejson"),
                "info_endpoint": stac.url_for(request, "info"),
                "statistics_endpoint": stac.url_for(request, "asset_statistics"),
            },
            media_type="text/html",
        )

    app.include_router(
        stac.router, prefix="/stac", tags=["SpatioTemporal Asset Catalog"]
    )

###############################################################################
# Mosaic endpoints
if not api_settings.disable_mosaic:
    mosaic = MosaicTilerFactory(router_prefix="/mosaicjson")
    app.include_router(mosaic.router, prefix="/mosaicjson", tags=["MosaicJSON"])

###############################################################################
# TileMatrixSets endpoints
tms = TMSFactory()
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
