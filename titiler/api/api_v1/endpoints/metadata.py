"""API metadata."""

from typing import Any, Dict, Optional, Union

import re
from functools import partial

import numpy

from rio_tiler.io import cogeo

from fastapi import APIRouter, Query
from starlette.requests import Request
from starlette.responses import Response
from starlette.concurrency import run_in_threadpool


_info = partial(run_in_threadpool, cogeo.info)
_bounds = partial(run_in_threadpool, cogeo.bounds)
_metadata = partial(run_in_threadpool, cogeo.metadata)
_spatial_info = partial(run_in_threadpool, cogeo.spatial_info)

router = APIRouter()


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


@router.get("/info", responses={200: {"description": "Return basic info on COG."}})
async def info(
    response: Response,
    url: str = Query(..., description="Cloud Optimized GeoTIFF URL."),
):
    """Handle /info requests."""
    response.headers["Cache-Control"] = "max-age=3600"
    return await _info(url)


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
        max_size=max_size,
        hist_options=hist_options,
        **kwargs,
    )
