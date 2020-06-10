"""titiler api."""

from titiler.api.endpoints import cog, tms

from fastapi import APIRouter

try:
    from titiler.api.endpoints import stac

    has_stac = True
except ModuleNotFoundError:
    has_stac = False


api_router = APIRouter()
api_router.include_router(cog.router, prefix="/cog", tags=["Cloud Optimized GeoTIFF"])

if has_stac:
    api_router.include_router(
        stac.router, prefix="/stac", tags=["SpatioTemporal Asset Catalog"]
    )

api_router.include_router(tms.router)
