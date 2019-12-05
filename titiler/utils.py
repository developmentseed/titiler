"""Titiler utility functions."""

from typing import Any, Tuple, BinaryIO

import os
import json
import hashlib

import numpy

from rio_color.operations import parse_operations
from rio_color.utils import scale_dtype, to_math_type
from rio_tiler.utils import linear_rescale, _chunks

from bmemcached import Client


def get_image_from_cache(img_hash: str, client: Client) -> BinaryIO:
    """Get image body from cache layer."""
    if os.getenv("DISABLE_CACHE"):
        return None

    try:
        return client.get(img_hash)
    except Exception:
        return None


def set_image_cache(
    img_hash: str, img_body: BinaryIO, client: Client, timeout: int = 432000
) -> bool:
    """Set base64 encoded image body in cache layer."""
    if os.getenv("DISABLE_CACHE"):
        return False

    try:
        client.set(img_hash, img_body, time=timeout)
    except Exception:
        return False

    return True


def get_hash(**kwargs: Any) -> str:
    """Create hash from a dict."""
    return hashlib.sha224(json.dumps(kwargs, sort_keys=True).encode()).hexdigest()


def postprocess_tile(
    tile: numpy.ndarray,
    mask: numpy.ndarray,
    rescale: str = None,
    color_formula: str = None,
) -> Tuple[numpy.ndarray, numpy.ndarray]:
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

    return tile, mask
