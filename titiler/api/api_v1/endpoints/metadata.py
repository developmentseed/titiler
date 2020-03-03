"""API metadata."""

from typing import Optional, Union

import os
import re
import urllib

import numpy
import rasterio
from rasterio import warp
from rio_tiler.mercator import get_zooms
from rio_tiler import main as cogTiler

from fastapi import APIRouter, Query
from starlette.requests import Request
from starlette.responses import Response


from titiler.core import config
from titiler.models.mapbox import TileJSON
from titiler.ressources.enums import ImageType

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
def tilejson(
    request: Request,
    response: Response,
    url: str = Query(..., title="Url of the COG"),
    tile_format: Optional[ImageType] = None,
    tile_scale: int = Query(1, gt=0, lt=4),
):
    """Handle /tilejson.json requests."""
    scheme = request.url.scheme
    host = request.headers["host"]
    if config.API_VERSION_STR:
        host += config.API_VERSION_STR

    kwargs = dict(request.query_params)
    kwargs.pop("tile_format", None)
    kwargs.pop("tile_scale", None)

    qs = urllib.parse.urlencode(list(kwargs.items()))
    if tile_format:
        tile_url = (
            f"{scheme}://{host}/{{z}}/{{x}}/{{y}}@{tile_scale}x.{tile_format}?{qs}"
        )
    else:
        tile_url = f"{scheme}://{host}/{{z}}/{{x}}/{{y}}@{tile_scale}x?{qs}"

    with rasterio.open(url) as src_dst:
        bounds = list(
            warp.transform_bounds(
                src_dst.crs, "epsg:4326", *src_dst.bounds, densify_pts=21
            )
        )
        minzoom, maxzoom = get_zooms(src_dst)
        center = [(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2, minzoom]

    response.headers["Cache-Control"] = "max-age=3600"
    return dict(
        bounds=bounds,
        center=center,
        minzoom=minzoom,
        maxzoom=maxzoom,
        name=os.path.basename(url),
        tiles=[tile_url],
    )


@router.get(
    "/bounds", responses={200: {"description": "Return the bounds of the COG."}}
)
def bounds(response: Response, url: str = Query(..., title="Url of the COG")):
    """Handle /bounds requests."""
    response.headers["Cache-Control"] = "max-age=3600"
    return cogTiler.bounds(url)


@router.get(
    "/metadata", responses={200: {"description": "Return the metadata of the COG."}}
)
def metadata(
    response: Response,
    url: str = Query(..., title="Url of the COG"),
    indexes: str = Query(None, title="Coma (',') delimited band indexes"),
    nodata: Union[str, int, float] = None,
    pmin: float = 2.0,
    pmax: float = 98.0,
    overview_level: int = Query(None, ge=0),
    max_size: int = 1024,
    histogram_bins: int = 20,
    histogram_range: int = None,
):
    """Handle /metadata requests."""
    if isinstance(indexes, str):
        indexes = tuple(int(s) for s in re.findall(r"\d+", indexes))

    if nodata is not None:
        nodata = numpy.nan if nodata == "nan" else float(nodata)

    response.headers["Cache-Control"] = "max-age=3600"
    return cogTiler.metadata(
        url,
        pmin=pmin,
        pmax=pmax,
        nodata=nodata,
        indexes=indexes,
        overview_level=overview_level,
        histogram_bins=histogram_bins,
        histogram_range=histogram_range,
    )
