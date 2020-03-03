"""titiler.api.utils."""

from typing import Any, Dict

import json
import hashlib

import numpy

from starlette.requests import Request

import mercantile
from rasterio.transform import from_bounds
from rasterio.crs import CRS

from rio_color.operations import parse_operations
from rio_color.utils import scale_dtype, to_math_type
from rio_tiler.utils import linear_rescale, _chunks

from titiler.db.memcache import CacheLayer


def get_cache(request: Request) -> CacheLayer:
    """Get Memcached Layer."""
    return request.state.cache


def get_hash(**kwargs: Any) -> str:
    """Create hash from a dict."""
    return hashlib.sha224(json.dumps(kwargs, sort_keys=True).encode()).hexdigest()


def get_geotiff_options(
    tile_x,
    tile_y,
    tile_z,
    data_type: str,
    tilesize: int = 256,
    dst_crs: CRS = CRS.from_epsg(3857),
) -> Dict:
    """GeoTIFF options."""
    bounds = mercantile.xy_bounds(mercantile.Tile(x=tile_x, y=tile_y, z=tile_z))
    dst_transform = from_bounds(*bounds, tilesize, tilesize)
    return dict(dtype=data_type, crs=dst_crs, transform=dst_transform)


def postprocess(
    tile: numpy.ndarray,
    mask: numpy.ndarray,
    rescale: str = None,
    color_formula: str = None,
) -> numpy.ndarray:
    """Post-process tile data."""
    if rescale:
        rescale_arr = list(map(float, rescale.split(",")))
        rescale_arr = list(_chunks(rescale_arr, 2))
        if len(rescale_arr) != tile.shape[0]:
            rescale_arr = ((rescale_arr[0]),) * tile.shape[0]

        for bdx in range(tile.shape[0]):
            tile[bdx] = numpy.where(
                mask,
                linear_rescale(
                    tile[bdx], in_range=rescale_arr[bdx], out_range=[0, 255]
                ),
                0,
            )
        tile = tile.astype(numpy.uint8)

    if color_formula:
        # make sure one last time we don't have
        # negative value before applying color formula
        tile[tile < 0] = 0
        for ops in parse_operations(color_formula):
            tile = scale_dtype(ops(to_math_type(tile)), numpy.uint8)

    return tile
