"""API tiles."""

from typing import Any, Dict, Union, Optional

import re
from io import BytesIO
from functools import partial

import numpy

from fastapi import APIRouter, Depends, Query, Path
from starlette.concurrency import run_in_threadpool

from rio_tiler.io import cogeo
from rio_tiler.colormap import get_colormap
from rio_tiler.utils import render, geotiff_options
from rio_tiler.profiles import img_profiles

from titiler.api import utils
from titiler.db.memcache import CacheLayer
from titiler.ressources.enums import ImageType
from titiler.ressources.common import drivers, mimetype
from titiler.ressources.responses import TileResponse


_tile = partial(run_in_threadpool, cogeo.tile)
_render = partial(run_in_threadpool, render)
_postprocess = partial(run_in_threadpool, utils.postprocess)


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
    responses=responses, tags=["tiles"], response_class=TileResponse
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
    bidx: Optional[str] = Query(None, description="Coma (',') delimited band indexes"),
    nodata: Optional[Union[str, int, float]] = Query(
        None, description="Overwrite internal Nodata value."
    ),
    rescale: Optional[str] = Query(
        None, description="Coma (',') delimited Min,Max bounds"
    ),
    color_formula: Optional[str] = Query(None, title="rio-color formula"),
    color_map: Optional[str] = Query(None, title="rio-tiler color map name"),
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
            bidx=bidx,
            nodata=nodata,
            rescale=rescale,
            color_formula=color_formula,
            color_map=color_map,
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
        indexes = tuple(int(s) for s in re.findall(r"\d+", bidx)) if bidx else None

        if nodata is not None:
            nodata = numpy.nan if nodata == "nan" else float(nodata)

        with utils.Timer() as t:
            tile, mask = await _tile(
                url, x, y, z, indexes=indexes, tilesize=tilesize, nodata=nodata
            )
        timings.append(("Read", t.elapsed))

        if not ext:
            ext = ImageType.jpg if mask.all() else ImageType.png

        with utils.Timer() as t:
            tile = await _postprocess(
                tile, mask, rescale=rescale, color_formula=color_formula
            )
        timings.append(("Post-process", t.elapsed))

        if color_map:
            color_map = get_colormap(color_map)

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

                content = await _render(
                    tile, mask, img_format=driver, colormap=color_map, **options
                )

        timings.append(("Format", t.elapsed))

        if cache_client and content:
            cache_client.set_image_cache(tile_hash, (content, ext))

    if timings:
        headers["X-Server-Timings"] = "; ".join(
            ["{} - {:0.2f}".format(name, time * 1000) for (name, time) in timings]
        )

    return TileResponse(content, media_type=mimetype[ext.value], headers=headers)
