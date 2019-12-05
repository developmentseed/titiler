"""Titiler app."""

from typing import Union, BinaryIO

import os
import re
import urllib

import numpy

import rasterio
from rasterio import warp
from rio_tiler import main as cogTiler
from rio_tiler.mercator import get_zooms
from rio_tiler.profiles import img_profiles
from rio_tiler.utils import array_to_image, get_colormap

from titiler import utils
from titiler import version
from titiler.templates.viewer import viewer_template

import bmemcached
from starlette.requests import Request
from starlette.responses import Response, HTMLResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi import FastAPI, Path, Query


MEMCACHE_HOST = os.environ.get("MEMCACHE_HOST")
MEMCACHE_USERNAME = os.environ.get("MEMCACHE_USERNAME")
MEMCACHE_PASSWORD = os.environ.get("MEMCACHE_PASSWORD")
MEMCACHE_PORT = os.environ.get("MEMCACHE_PORT", "11211")
if MEMCACHE_HOST and MEMCACHE_USERNAME and MEMCACHE_PASSWORD:
    cache_client = bmemcached.Client(
        (f"{MEMCACHE_HOST}:{MEMCACHE_PORT}",), MEMCACHE_USERNAME, MEMCACHE_PASSWORD
    )
else:
    cache_client = None


app = FastAPI(
    title="titiler",
    description="A lightweight Cloud Optimized GeoTIFF tile server",
    version=version,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=0)


def TileResponse(content: BinaryIO, media_type: str, ttl: int = 3600) -> Response:
    """Binary tile response."""
    headers = {"Content-Type": f"image/{media_type}"}
    if ttl:
        headers["Cache-Control"] = f"max-age={ttl}"

    return Response(
        content=content,
        status_code=200,
        headers=headers,
        media_type=f"image/{media_type}",
    )


@app.get(
    "/{z}/{x}/{y}\\.{ext}",
    responses={
        200: {
            "content": {
                "image/png": {},
                "image/jpg": {},
                "image/webp": {},
                "image/tiff": {},
            },
            "description": "Return an image.",
        }
    },
    description="Read COG and return an image tile",
)
def tile(
    z: int,
    x: int,
    y: int,
    ext: str = Path(..., regex="^(png)|(jpg)|(webp)|(tif)$"),
    scale: int = 1,
    url: str = Query(..., title="Url of the COG"),
    indexes: str = Query(None, title="Coma (',') delimited band indexes"),
    nodata: Union[str, int, float] = None,
    rescale: str = Query(None, title="Coma (',') delimited Min,Max bounds"),
    color_formula: str = Query(None, title="rio-color formula"),
    color_map: str = Query(None, title="rio-tiler color map names"),
):
    """Handle /tiles requests."""
    tile_hash = utils.get_hash(
        **dict(
            z=z,
            x=x,
            y=y,
            ext=ext,
            scale=scale,
            url=url,
            indexes=indexes,
            nodata=nodata,
            rescale=rescale,
            color_formula=color_formula,
            color_map=color_map,
        )
    )

    img = (
        utils.get_image_from_cache(tile_hash, client=cache_client)
        if cache_client
        else None
    )
    if not img:
        if isinstance(indexes, str):
            indexes = tuple(int(s) for s in re.findall(r"\d+", indexes))

        if nodata is not None:
            nodata = numpy.nan if nodata == "nan" else float(nodata)

        tilesize = scale * 256
        tile, mask = cogTiler.tile(
            url, x, y, z, indexes=indexes, tilesize=tilesize, nodata=nodata
        )

        rtile, _ = utils.postprocess_tile(
            tile, mask, rescale=rescale, color_formula=color_formula
        )

        if color_map:
            color_map = get_colormap(color_map, format="gdal")

        driver = "jpeg" if ext == "jpg" else ext
        options = img_profiles.get(driver, {})
        img = array_to_image(
            rtile, mask, img_format=driver, color_map=color_map, **options
        )

        if cache_client:
            utils.set_image_cache(tile_hash, img, client=cache_client)

    return TileResponse(img, media_type=ext)


@app.get(
    "/tilejson.json",
    responses={200: {"description": "Return a tilejson map metadata."}},
)
def tilejson(
    request: Request,
    response: Response,
    url: str = Query(..., title="Url of the COG"),
    tile_format: str = Query("png", regex="^(png)|(jpg)|(webp)|(pbf)$"),
):
    """Handle /tilejson.json requests."""
    host = request.headers["host"]
    scheme = request.url.scheme
    kwargs = dict(request.query_params)
    kwargs.pop("tile_format", None)

    qs = urllib.parse.urlencode(list(kwargs.items()))
    tile_url = f"{scheme}://{host}/{{z}}/{{x}}/{{y}}.{tile_format}?{qs}"

    with rasterio.open(url) as src_dst:
        bounds = warp.transform_bounds(
            *[src_dst.crs, "epsg:4326"] + list(src_dst.bounds), densify_pts=21
        )
        center = [(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2]
        minzoom, maxzoom = get_zooms(src_dst)

    response.headers["Cache-Control"] = "max-age=3600"
    return dict(
        bounds=bounds,
        center=center,
        minzoom=minzoom,
        maxzoom=maxzoom,
        name=os.path.basename(url),
        tilejson="2.1.0",
        tiles=[tile_url],
    )


@app.get("/bounds", responses={200: {"description": "Return the bounds of the COG."}})
def bounds(response: Response, url: str = Query(..., title="Url of the COG")):
    """Handle /bounds requests."""
    response.headers["Cache-Control"] = "max-age=3600"
    return cogTiler.bounds(url)


@app.get(
    "/metadata", responses={200: {"description": "Return the metadata of the COG."}}
)
def metadata(
    response: Response,
    url: str = Query(..., title="Url of the COG"),
    pmin: float = 2.0,
    pmax: float = 98.0,
    nodata: Union[str, int, float] = None,
    indexes: str = Query(None, title="Coma (',') delimited band indexes"),
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


@app.get(
    "/",
    responses={200: {"description": "Simple COG viewer."}},
    response_class=HTMLResponse,
)
def viewer(request: Request, response: Response):
    """Handle /requests."""
    host = request.headers["host"]
    scheme = request.url.scheme
    return viewer_template(f"{scheme}://{host}")
