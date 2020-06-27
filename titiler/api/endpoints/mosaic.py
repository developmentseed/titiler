"""API for MosaicJSON Dataset."""
import asyncio
import os
import random
from functools import partial
from io import BytesIO
from typing import Callable, Sequence

import mercantile
import numpy
from cogeo_mosaic.backends import MosaicBackend
from cogeo_mosaic.mosaic import MosaicJSON
from cogeo_mosaic.utils import get_footprints
from rasterio.crs import CRS
from rasterio.transform import from_bounds
from rio_tiler.io.cogeo import tile as cogeoTiler
from rio_tiler.profiles import img_profiles
from rio_tiler.utils import render

from titiler.api.deps import CommonTileParams
from titiler.api.endpoints.cog import cog_info, tile_response_codes
from titiler.api.utils import postprocess
from titiler.models.metadata import cogBounds, cogInfo
from titiler.models.mosaic import CreateMosaicJSON, UpdateMosaicJSON
from titiler.ressources.common import drivers
from titiler.ressources.enums import ImageMimeTypes, ImageType, PixelSelectionMethod
from titiler.ressources.responses import ImgResponse

from fastapi import APIRouter, Depends, Path, Query
from fastapi.routing import APIRoute

from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response


def _chunks(my_list: Sequence, chuck_size: int):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(my_list), chuck_size):
        yield my_list[i : i + chuck_size]


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


@router.get(r"/tiles/{z}/{x}/{y}", **tile_response_codes)
@router.get(r"/tiles/{z}/{x}/{y}\.{format}", **tile_response_codes)
@router.get(r"/tiles/{z}/{x}/{y}@{scale}x", **tile_response_codes)
@router.get(r"/tiles/{z}/{x}/{y}@{scale}x\.{format}", **tile_response_codes)
async def mosaic_tile(
    z: int = Path(..., ge=0, le=30, description="Mercator tiles's zoom level"),
    x: int = Path(..., description="Mercator tiles's column"),
    y: int = Path(..., description="Mercator tiles's row"),
    scale: int = Query(
        1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
    ),
    format: ImageType = Query(None, description="Output image type. Default is auto."),
    url: str = Query(..., description="Cloud Optimized GeoTIFF URL."),
    pixel_selection: PixelSelectionMethod = Query(
        PixelSelectionMethod.first, description="Pixel selection method."
    ),
    image_params: CommonTileParams = Depends(),
):
    """Read MosaicJSON tile"""
    # TODO: Maybe use ``read_mosaic`` defined above (depending on cache behavior which is still TBD)
    pixsel = pixel_selection.method()

    with MosaicBackend(url) as mosaic:
        assets = mosaic.tile(x=x, y=y, z=z)

    tilesize = 256 * scale

    # Rio-tiler-mosaic uses an external ThreadPoolExecutor to process multiple assets at once but we want to use the
    # executor provided by the event loop.  Instead of calling ``rio_tiler_mosaic.mosaic.mosaic_tiler`` directly we will
    # transcribe the code here and use the executor provided by the event loop.  This also means we define this function
    # as a coroutine (even though nothing that is called is a coroutine), since the event loop's executor isn't
    # available in normal ``def`` functions.
    # https://github.com/cogeotiff/rio-tiler-mosaic/blob/master/rio_tiler_mosaic/mosaic.py#L37-L102
    _tiler = partial(
        cogeoTiler,
        tile_x=x,
        tile_y=y,
        tile_z=z,
        tilesize=tilesize,
        indexes=image_params.indexes,
        # expression=image_params.expression, # TODO: Figure out why expression kwarg doesn't work
        nodata=image_params.nodata,
        **image_params.kwargs
    )
    futures = [run_in_threadpool(_tiler, asset) for asset in assets]

    semaphore = asyncio.Semaphore(int(os.getenv("MOSAIC_CONCURRENCY", 10)))

    async with semaphore:
        for fut in asyncio.as_completed(futures):
            try:
                tile, mask = await fut
            except Exception:
                # Gracefully handle exceptions
                continue

            tile = numpy.ma.array(tile)
            tile.mask = mask == 0
            pixsel.feed(tile)
            if pixsel.is_done:
                break

    # TODO: Raise exception if tile is empty

    # TODO: Most of the code below may be deduped with /cog/tiles endpoint
    if not format:
        format = ImageType.jpg if mask.all() else ImageType.png

    tile = postprocess(
        tile,
        mask,
        rescale=image_params.rescale,
        color_formula=image_params.color_formula,
    )

    if format == ImageType.npy:
        sio = BytesIO()
        numpy.save(sio, (tile, mask))
        sio.seek(0)
        content = sio.getvalue()
    else:
        driver = drivers[format.value]
        options = img_profiles.get(driver.lower(), {})
        if format == ImageType.tif:
            bounds = mercantile.xy_bounds(mercantile.Tile(x, y, z))
            dst_transform = from_bounds(*bounds, tilesize, tilesize)
            options = {"crs": CRS.from_epsg("3857"), "transform": dst_transform}
        content = render(tile, mask, img_format=driver, **options)

    return ImgResponse(content, media_type=ImageMimeTypes[format.value].value)
