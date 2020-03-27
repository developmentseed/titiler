"""API metadata."""

from typing import Any, Dict, Optional, Union

import os
import re
from functools import partial
from urllib.parse import urlencode

import numpy

from rio_tiler.io import cogeo

from fastapi import APIRouter, Query
from starlette.requests import Request
from starlette.responses import Response
from starlette.concurrency import run_in_threadpool

from titiler.core import config
from titiler.models.mapbox import TileJSON
from titiler.ressources.enums import ImageType


_bounds = partial(run_in_threadpool, cogeo.bounds)
_metadata = partial(run_in_threadpool, cogeo.metadata)
_spatial_info = partial(run_in_threadpool, cogeo.spatial_info)

router = APIRouter()


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


@router.get(
    "/bounds", responses={200: {"description": "Return the bounds of the COG."}}
)
async def bounds(
    response: Response,
    url: str = Query(..., description="Cloud Optimized GeoTIFF URL."),
):
    """Handle /bounds requests."""
    response.headers["Cache-Control"] = "max-age=3600"
    return await _bounds(url)


@router.get(
    "/metadata", responses={200: {"description": "Return the metadata of the COG."}}
)
async def metadata(
    request: Request,
    response: Response,
    url: str = Query(..., description="Cloud Optimized GeoTIFF URL."),
    bidx: Optional[str] = Query(None, description="Coma (',') delimited band indexes"),
    nodata: Optional[Union[str, int, float]] = Query(
        None, description="Overwrite internal Nodata value."
    ),
    pmin: float = 2.0,
    pmax: float = 98.0,
    max_size: int = 1024,
    histogram_bins: int = 20,
    histogram_range: Optional[str] = Query(
        None, description="Coma (',') delimited Min,Max bounds"
    ),
):
    """Handle /metadata requests."""
    kwargs = dict(request.query_params)
    kwargs.pop("url", None)
    kwargs.pop("bidx", None)
    kwargs.pop("nodata", None)
    kwargs.pop("pmin", None)
    kwargs.pop("pmax", None)
    kwargs.pop("max_size", None)
    kwargs.pop("histogram_bins", None)
    kwargs.pop("histogram_range", None)

    indexes = tuple(int(s) for s in re.findall(r"\d+", bidx)) if bidx else None

    if nodata is not None:
        nodata = numpy.nan if nodata == "nan" else float(nodata)

    hist_options: Dict[str, Any] = dict()
    if histogram_bins:
        hist_options.update(dict(bins=histogram_bins))
    if histogram_range:
        hist_options.update(dict(range=list(map(float, histogram_range.split(",")))))

    response.headers["Cache-Control"] = "max-age=3600"
    return await _metadata(
        url,
        pmin,
        pmax,
        nodata=nodata,
        indexes=indexes,
        hist_options=hist_options,
        **kwargs,
    )
