"""API tiles."""

from typing import Any, Dict, Optional

import os
from io import BytesIO
from functools import partial
from urllib.parse import urlencode

import numpy

from fastapi import APIRouter, Depends, Query, Path
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import Response

from rio_tiler.io import cogeo
from rio_tiler.utils import render, geotiff_options
from rio_tiler.profiles import img_profiles

from titiler.api import utils
from titiler.api.deps import CommonImageParams
from titiler.db.memcache import CacheLayer
from titiler.ressources.enums import ImageType
from titiler.ressources.common import drivers, mimetype
from titiler.ressources.responses import TileResponse
from titiler.core import config
from titiler.models.mapbox import TileJSON


_tile = partial(run_in_threadpool, cogeo.tile)
_render = partial(run_in_threadpool, render)
_postprocess = partial(run_in_threadpool, utils.postprocess)
_spatial_info = partial(run_in_threadpool, cogeo.spatial_info)


router = APIRouter()
responses = {
    200: {
        "content": {
            "image/png": {},
            "image/jpg": {},
            "image/webp": {},
            "image/tiff": {},
            "application/x-binary": {},
        },
        "description": "Return an image.",
    }
}
tile_routes_params: Dict[str, Any] = dict(
    responses=responses, response_class=TileResponse
)


@router.get(r"/{z}/{x}/{y}", **tile_routes_params)
@router.get(r"/{z}/{x}/{y}\.{ext}", **tile_routes_params)
@router.get(r"/{z}/{x}/{y}@{scale}x", **tile_routes_params)
@router.get(r"/{z}/{x}/{y}@{scale}x\.{ext}", **tile_routes_params)
async def tile(
    z: int = Path(..., ge=0, le=30, description="Mercator tiles's zoom level"),
    x: int = Path(..., description="Mercator tiles's column"),
    y: int = Path(..., description="Mercator tiles's row"),
    scale: int = Query(
        1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
    ),
    ext: ImageType = Query(None, description="Output image type. Default is auto."),
    url: str = Query(..., description="Cloud Optimized GeoTIFF URL."),
    image_params: CommonImageParams = Depends(CommonImageParams),
    cache_client: CacheLayer = Depends(utils.get_cache),
) -> TileResponse:
    """Handle /tiles requests."""
    timings = []
    headers: Dict[str, str] = {}

    tile_hash = utils.get_hash(
        **dict(
            z=z,
            x=x,
            y=y,
            ext=ext,
            scale=scale,
            url=url,
            indexes=image_params.indexes,
            nodata=image_params.nodata,
            rescale=image_params.rescale,
            color_formula=image_params.color_formula,
            color_map=image_params.color_map,
        )
    )
    tilesize = scale * 256

    content = None
    if cache_client:
        try:
            content, ext = cache_client.get_image_from_cache(tile_hash)
            headers["X-Cache"] = "HIT"
        except Exception:
            content = None

    if not content:
        with utils.Timer() as t:
            tile, mask = await _tile(
                url,
                x,
                y,
                z,
                indexes=image_params.indexes,
                tilesize=tilesize,
                nodata=image_params.nodata,
            )
        timings.append(("Read", t.elapsed))

        if not ext:
            ext = ImageType.jpg if mask.all() else ImageType.png

        with utils.Timer() as t:
            tile = await _postprocess(
                tile,
                mask,
                rescale=image_params.rescale,
                color_formula=image_params.color_formula,
            )
        timings.append(("Post-process", t.elapsed))

        with utils.Timer() as t:
            if ext == ImageType.npy:
                sio = BytesIO()
                numpy.save(sio, (tile, mask))
                sio.seek(0)
                content = sio.getvalue()
            else:
                driver = drivers[ext.value]
                options = img_profiles.get(driver.lower(), {})
                if ext == ImageType.tif:
                    options = geotiff_options(x, y, z, tilesize=tilesize)

                if image_params.color_map:
                    options["colormap"] = image_params.color_map

                content = await _render(tile, mask, img_format=driver, **options)

        timings.append(("Format", t.elapsed))

        if cache_client and content:
            cache_client.set_image_cache(tile_hash, (content, ext))

    if timings:
        headers["X-Server-Timings"] = "; ".join(
            ["{} - {:0.2f}".format(name, time * 1000) for (name, time) in timings]
        )

    return TileResponse(content, media_type=mimetype[ext.value], headers=headers)


@router.get(
    "/tilejson.json",
    response_model=TileJSON,
    responses={200: {"description": "Return a tilejson"}},
    response_model_include={
        "tilejson",
        "scheme",
        "version",
        "minzoom",
        "maxzoom",
        "bounds",
        "center",
        "tiles",
    },  # https://github.com/tiangolo/fastapi/issues/528#issuecomment-589659378
)
async def tilejson(
    request: Request,
    response: Response,
    url: str = Query(..., description="Cloud Optimized GeoTIFF URL."),
    tile_format: Optional[ImageType] = Query(
        None, description="Output image type. Default is auto."
    ),
    tile_scale: int = Query(
        1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
    ),
):
    """Handle /tilejson.json requests."""
    scheme = request.url.scheme
    host = request.headers["host"]
    if config.API_VERSION_STR:
        host += config.API_VERSION_STR

    kwargs = dict(request.query_params)
    kwargs.pop("tile_format", None)
    kwargs.pop("tile_scale", None)

    qs = urlencode(list(kwargs.items()))
    if tile_format:
        tile_url = (
            f"{scheme}://{host}/{{z}}/{{x}}/{{y}}@{tile_scale}x.{tile_format}?{qs}"
        )
    else:
        tile_url = f"{scheme}://{host}/{{z}}/{{x}}/{{y}}@{tile_scale}x?{qs}"

    meta = await _spatial_info(url)
    response.headers["Cache-Control"] = "max-age=3600"
    return dict(
        bounds=meta["bounds"],
        center=meta["center"],
        minzoom=meta["minzoom"],
        maxzoom=meta["maxzoom"],
        name=os.path.basename(url),
        tiles=[tile_url],
    )
