"""titiler api."""
import importlib

from titiler.api.endpoints import cog, tms

from fastapi import APIRouter


def _include_extra_router(router: APIRouter, module: str, **kwargs) -> None:
    """Helper function to add routers available through pip extras"""
    try:
        mod = importlib.import_module(module)
        router.include_router(mod.router, **kwargs)  # type: ignore
    except ModuleNotFoundError:
        pass


api_router = APIRouter()
api_router.include_router(cog.router, prefix="/cog", tags=["Cloud Optimized GeoTIFF"])
api_router.include_router(tms.router)

# Additional routers installed as pip extras
_include_extra_router(
    api_router,
    module="titiler.api.endpoints.stac",
    prefix="/stac",
    tags=["SpatioTemporal Asset Catalog"],
)
_include_extra_router(
    api_router,
    module="titiler.api.endpoints.mosaic",
    prefix="/mosaicjson",
    tags=["MosaicJSON"],
)
