"""API for MosaicJSON Dataset."""
import random

import mercantile
from cogeo_mosaic.backends import MosaicBackend
from cogeo_mosaic.mosaic import MosaicJSON
from cogeo_mosaic.utils import get_footprints

from titiler.api.endpoints.cog import cog_info
from titiler.models.metadata import cogBounds, cogInfo
from titiler.models.mosaic import CreateMosaicJSON, UpdateMosaicJSON

from fastapi import APIRouter, Query

from starlette.responses import Response

router = APIRouter()


@router.post(
    "", response_model=MosaicJSON, response_model_exclude_none=True,
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
    "",
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


@router.put("", response_model=MosaicJSON, response_model_exclude_none=True)
def update_mosaicjson(body: UpdateMosaicJSON):
    """Update an existing MosaicJSON"""
    with MosaicBackend(body.url) as mosaic:
        features = get_footprints(body.files, max_threads=body.max_threads)
        mosaic.update(features, add_first=body.add_first, quiet=True)
        return mosaic.mosaic_def


@router.get(
    "/bounds",
    response_model=cogBounds,
    responses={200: {"description": "Return the bounds of the MosaicJSON"}},
)
def mosaicjson_bounds(
    resp: Response, url: str = Query(..., description="MosaicJSON URL")
):
    """Read MosaicJSON bounds"""
    resp.headers["Cache-Control"] = "max-age=3600"
    with MosaicBackend(url) as mosaic:
        return {"bounds": mosaic.mosaic_def.bounds}


@router.get("/info", response_model=cogInfo)
def mosaicjson_info(
    resp: Response, url: str = Query(..., description="MosaicJSON URL")
):
    """
    Read MosaicJSON info

    Ref: https://github.com/developmentseed/cogeo-mosaic-tiler/blob/master/cogeo_mosaic_tiler/handlers/app.py#L164-L198
    """
    with MosaicBackend(url) as mosaic:
        meta = mosaic.metadata
        response = {
            "bounds": meta["bounds"],
            "center": meta["center"],
            "maxzoom": meta["maxzoom"],
            "minzoom": meta["minzoom"],
            "name": url,
        }
        if not url.startswith("dynamodb://"):
            mosaic_quadkeys = set(mosaic._quadkeys)
            tile = mercantile.quadkey_to_tile(random.sample(mosaic_quadkeys, 1)[0])
            assets = mosaic.tile(*tile)
            asset_info = cog_info(resp, url=assets[0])
            del asset_info["band_metadata"]
            response["quadkeys"] = list(mosaic_quadkeys)
            response = {**asset_info, **response}
        return response
