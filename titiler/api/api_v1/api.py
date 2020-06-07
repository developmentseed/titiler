"""titiler api."""

from fastapi import APIRouter

from titiler.api.api_v1.endpoints import cog, tms

try:
    from titiler.api.api_v1.endpoints import stac

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
