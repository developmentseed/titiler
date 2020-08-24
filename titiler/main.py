"""titiler app."""
import importlib

from rio_cogeo.cogeo import cog_info as rio_cogeo_info
from rio_tiler_crs import STACReader

from . import settings, version
from .db.memcache import CacheLayer
from .dependencies import PathParams
from .endpoints import demo, tms
from .endpoints.factory import TilerFactory
from .errors import DEFAULT_STATUS_CODES, add_exception_handlers
from .models.cog import RioCogeoInfo

from fastapi import Depends, FastAPI, Query

from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request

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

cog = TilerFactory(router_prefix="cog")


@cog.router.get("/validate", response_model=RioCogeoInfo)
def cog_validate(
    src_path: PathParams = Depends(),
    strict: bool = Query(False, description="Treat warnings as errors"),
):
    """Validate a COG"""
    return rio_cogeo_info(src_path.url, strict=strict)


app.include_router(cog.router, prefix="/cog", tags=["Cloud Optimized GeoTIFF"])


stac = TilerFactory(reader=STACReader, add_asset_deps=True, router_prefix="stac")
app.include_router(stac.router, prefix="/stac", tags=["SpatioTemporal Asset Catalog"])


try:
    fact = importlib.import_module("titiler.endpoints.factory_mosaic")
    mosaic = fact.MosaicTilerFactory(router_prefix="mosaicjson")  # type: ignore
    app.include_router(mosaic.router, prefix="/mosaicjson", tags=["MosaicJSON"])
except ModuleNotFoundError:
    pass


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
