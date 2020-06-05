"""titiler api."""

from fastapi import APIRouter

from titiler.api.api_v1.endpoints import tiles, metadata, ogc  # , operations

api_router = APIRouter()
api_router.include_router(tiles.router)
api_router.include_router(metadata.router)
api_router.include_router(ogc.router)
# api_router.include_router(operations.router, tags=["operations"])
