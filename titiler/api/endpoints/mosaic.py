"""API for MosaicJSON Dataset."""
import random
from typing import Callable

import mercantile
from cogeo_mosaic.backends import MosaicBackend
from cogeo_mosaic.mosaic import MosaicJSON
from cogeo_mosaic.utils import get_footprints

from titiler.api.endpoints.cog import cog_info
from titiler.models.metadata import cogBounds, cogInfo
from titiler.models.mosaic import CreateMosaicJSON, UpdateMosaicJSON

from fastapi import APIRouter, Query
from fastapi.routing import APIRoute

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response


class MosaicJSONRouter(APIRoute):
    """Custom router to temporarily forbid usage of cogeo-mosaic STAC backend"""

    def get_route_handler(self) -> Callable:
        """Override base method (https://fastapi.tiangolo.com/advanced/custom-request-and-route/)"""
        original_route_handler = super().get_route_handler()

        async def forbid_stac_backend(request: Request) -> Response:
            url = request.query_params.get("url")
            if not url:
                body = await request.json()
                url = body.get("url")
            if url.startswith("stac"):
                # Raise as a validation error
                raise HTTPException(
                    status_code=422,
                    detail="STAC is not currently supported for mosaicjson endpoints",
                )
            return await original_route_handler(request)

        return forbid_stac_backend


router = APIRouter(route_class=MosaicJSONRouter)


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
