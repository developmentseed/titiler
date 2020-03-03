"""API tiles."""

from typing import Union

import re
from io import BytesIO

import numpy

from fastapi import APIRouter, Depends, Query

from rio_tiler import main as cogTiler
from rio_tiler.profiles import img_profiles
from rio_tiler.utils import array_to_image, get_colormap


from titiler.api import utils
from titiler.db.memcache import CacheLayer
from titiler.ressources.enums import ImageType
from titiler.ressources.common import drivers, mimetype
from titiler.ressources.responses import TileResponse

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
tile_routes_params = dict(
    responses=responses, tags=["tiles"], response_class=TileResponse
)


@router.get(r"/{z}/{x}/{y}", **tile_routes_params)
@router.get(r"/{z}/{x}/{y}\.{ext}", **tile_routes_params)
@router.get(r"/{z}/{x}/{y}@{scale}x", **tile_routes_params)
@router.get(r"/{z}/{x}/{y}@{scale}x\.{ext}", **tile_routes_params)
def tile(
    z: int,
    x: int,
    y: int,
    scale: int = Query(1, gt=0, lt=4),
    ext: ImageType = None,
    url: str = Query(..., title="Url of the COG"),
    bidx: str = Query(None, title="Coma (',') delimited band indexes"),
    nodata: Union[str, int, float] = None,
    rescale: str = Query(None, title="Coma (',') delimited Min,Max bounds"),
    color_formula: str = Query(None, title="rio-color formula"),
    color_map: str = Query(None, title="rio-tiler color map names"),
    cache_client: CacheLayer = Depends(utils.get_cache),
) -> TileResponse:
    """Handle /tiles requests."""
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

    content = None
    if cache_client:
        try:
            content, ext = cache_client.get_image_from_cache(tile_hash)
        except Exception:
            content = None

    if not content:
        indexes = tuple(int(s) for s in re.findall(r"\d+", bidx)) if bidx else None

        if nodata is not None:
            nodata = numpy.nan if nodata == "nan" else float(nodata)

        tilesize = scale * 256
        tile, mask = cogTiler.tile(
            url, x, y, z, indexes=indexes, tilesize=tilesize, nodata=nodata
        )
        if not ext:
            ext = ImageType.jpg if mask.all() else ImageType.png

        tile = utils.postprocess(
            tile, mask, rescale=rescale, color_formula=color_formula
        )

        if color_map:
            color_map = get_colormap(color_map, format="gdal")

        if ext == "npy":
            sio = BytesIO()
            numpy.save(sio, (tile, mask))
            sio.seek(0)
            content = sio.getvalue()
        else:
            driver = drivers[ext]
            options = img_profiles.get(driver.lower(), {})
            if ext == "tif":
                options = utils.get_geotiff_options(
                    x, y, z, tile.dtype, tilesize=tilesize
                )

            content = array_to_image(
                tile, mask, img_format=driver, color_map=color_map, **options
            )

        if cache_client and content:
            cache_client.set_image_cache(tile_hash, (content, ext))

    return TileResponse(content, media_type=mimetype[ext.value])
