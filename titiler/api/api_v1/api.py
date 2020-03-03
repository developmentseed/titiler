"""titiler api."""

from fastapi import APIRouter

from titiler.api.api_v1.endpoints import tiles, metadata, ogc, viewer  # , operations

api_router = APIRouter()
api_router.include_router(viewer.router, tags=["UI"])
api_router.include_router(tiles.router, tags=["tiles"])
api_router.include_router(metadata.router, tags=["metadata"])
api_router.include_router(ogc.router, tags=["OGC"])
# api_router.include_router(operations.router, tags=["operations"])
