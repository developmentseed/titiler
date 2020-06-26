"""API for MosaicJSON Dataset."""
from cogeo_mosaic.backends import MosaicBackend
from cogeo_mosaic.mosaic import MosaicJSON
from cogeo_mosaic.utils import get_footprints

from titiler.models.mosaic import CreateMosaicJSON, UpdateMosaicJSON

from fastapi import APIRouter, Query

from starlette.responses import Response

router = APIRouter()


@router.post(
    "/mosaicjson", response_model=MosaicJSON, response_model_exclude_none=True,
)
def create_mosaicjson(body: CreateMosaicJSON):
    """Create a MosaicJSON"""
    mosaic = MosaicJSON.from_urls(
        body.files,
        minzoom=body.minzoom,
        maxzoom=body.maxzoom,
        max_threads=body.max_threads,
    )
    with MosaicBackend(body.url, mosaic_def=mosaic) as mosaic:
        mosaic.write()
        return mosaic.mosaic_def


@router.get(
    "/mosaicjson",
    response_model=MosaicJSON,
    response_model_exclude_none=True,
    responses={200: {"description": "Return MosaicJSON definition"}},
)
def read_mosaicjson(
    resp: Response, url: str = Query(..., description="MosaicJSON URL")
):
    """Read a MosaicJSON"""
    resp.headers["Cache-Control"] = "max-age-3600"
    with MosaicBackend(url) as mosaic:
        return mosaic.mosaic_def


@router.put("/mosaicjson", response_model=MosaicJSON, response_model_exclude_none=True)
def update_mosaicjson(body: UpdateMosaicJSON):
    """Update an existing MosaicJSON"""
    with MosaicBackend(body.url) as mosaic:
        features = get_footprints(body.files, max_threads=body.max_threads)
        mosaic.update(features, add_first=body.add_first, quiet=True)
        return mosaic.mosaic_def
