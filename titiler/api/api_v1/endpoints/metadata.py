"""API metadata."""

from typing import Any, Dict, Optional, Union

import re

import numpy

from rio_tiler_crs import COGReader

from fastapi import APIRouter, Query
from starlette.requests import Request
from starlette.responses import Response

router = APIRouter()


@router.get(
    "/cog/bounds", responses={200: {"description": "Return the bounds of the COG."}}
)
async def bounds(
    resp: Response, url: str = Query(..., description="Cloud Optimized GeoTIFF URL."),
):
    """Handle /bounds requests."""
    resp.headers["Cache-Control"] = "max-age=3600"
    with COGReader(url) as cog:
        return {"bounds": cog.bounds}


@router.get("/cog/info", responses={200: {"description": "Return basic info on COG."}})
async def info(
    resp: Response, url: str = Query(..., description="Cloud Optimized GeoTIFF URL.")
):
    """Handle /info requests."""
    resp.headers["Cache-Control"] = "max-age=3600"
    with COGReader(url) as cog:
        info = cog.info
    info.pop("maxzoom", None)  # We don't use TMS here
    info.pop("minzoom", None)  # We don't use TMS here
    info.pop("center", None)  # We don't use TMS here
    return info


@router.get(
    "/cog/metadata",
    responses={200: {"description": "Return the metadata of the COG."}},
)
async def metadata(
    request: Request,
    resp: Response,
    url: str = Query(..., description="Cloud Optimized GeoTIFF URL."),
    bidx: Optional[str] = Query(None, description="Coma (',') delimited band indexes"),
    nodata: Optional[Union[str, int, float]] = Query(
        None, description="Overwrite internal Nodata value."
    ),
    pmin: float = Query(2.0, description="Minimum percentile"),
    pmax: float = Query(98.0, description="Maximum percentile"),
    max_size: int = Query(1024, description="Maximum image size to read onto."),
    histogram_bins: Optional[int] = None,
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

    with COGReader(url) as cog:
        info = cog.info
        info.pop("maxzoom", None)  # We don't use TMS here
        info.pop("minzoom", None)  # We don't use TMS here
        info.pop("center", None)  # We don't use TMS here
        stats = cog.stats(
            pmin,
            pmax,
            nodata=nodata,
            indexes=indexes,
            max_size=max_size,
            hist_options=hist_options,
            **kwargs,
        )
        info["statistics"] = stats

    resp.headers["Cache-Control"] = "max-age=3600"
    return info
