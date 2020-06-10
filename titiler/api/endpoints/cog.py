"""API for Cloud Optimized GeoTIFF Dataset."""

import os
from io import BytesIO
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import numpy
from rasterio.transform import from_bounds
from rio_tiler.profiles import img_profiles
from rio_tiler.utils import render
from rio_tiler_crs import COGReader

from titiler.api import utils
from titiler.api.deps import (
    CommonImageParams,
    CommonMetadataParams,
    TileMatrixSetNames,
    morecantile,
)
from titiler.db.memcache import CacheLayer
from titiler.models.mapbox import TileJSON
from titiler.models.metadata import cogBounds, cogInfo, cogMetadata
from titiler.ressources.common import drivers
from titiler.ressources.enums import ImageMimeTypes, ImageType, MimeTypes
from titiler.ressources.responses import TileResponse, XMLResponse
from titiler.templates.factory import web_template

from fastapi import APIRouter, Depends, Path, Query

from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from starlette.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="titiler/templates")


@router.get(
    "/bounds",
    response_model=cogBounds,
    responses={200: {"description": "Return the bounds of the COG."}},
)
async def cog_bounds(
    resp: Response, url: str = Query(..., description="Cloud Optimized GeoTIFF URL."),
):
    """Return the bounds of the COG."""
    resp.headers["Cache-Control"] = "max-age=3600"
    with COGReader(url) as cog:
        return {"bounds": cog.bounds}


@router.get(
    "/info",
    response_model=cogInfo,
    response_model_exclude={"minzoom", "maxzoom", "center"},
    response_model_exclude_none=True,
    responses={200: {"description": "Return basic info on COG."}},
)
async def cog_info(
    resp: Response, url: str = Query(..., description="Cloud Optimized GeoTIFF URL.")
):
    """Return basic info on COG."""
    resp.headers["Cache-Control"] = "max-age=3600"
    with COGReader(url) as cog:
        info = cog.info
    return info


@router.get(
    "/metadata",
    response_model=cogMetadata,
    response_model_exclude={"minzoom", "maxzoom", "center"},
    response_model_exclude_none=True,
    responses={200: {"description": "Return the metadata of the COG."}},
)
async def cog_metadata(
    request: Request,
    resp: Response,
    url: str = Query(..., description="Cloud Optimized GeoTIFF URL."),
    metadata_params: CommonMetadataParams = Depends(CommonMetadataParams),
):
    """Return the metadata of the COG."""
    kwargs = dict(request.query_params)
    kwargs.pop("url", None)
    kwargs.pop("bidx", None)
    kwargs.pop("nodata", None)
    kwargs.pop("pmin", None)
    kwargs.pop("pmax", None)
    kwargs.pop("max_size", None)
    kwargs.pop("histogram_bins", None)
    kwargs.pop("histogram_range", None)

    with COGReader(url) as cog:
        info = cog.info
        stats = cog.stats(
            metadata_params.pmin,
            metadata_params.pmax,
            nodata=metadata_params.nodata,
            indexes=metadata_params.indexes,
            max_size=metadata_params.max_size,
            hist_options=metadata_params.hist_options,
            **kwargs,
        )
        info["statistics"] = stats

    resp.headers["Cache-Control"] = "max-age=3600"
    return info


params: Dict[str, Any] = {
    "responses": {
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
    },
    "response_class": TileResponse,
}


@router.get(r"/tiles/{z}/{x}/{y}", **params)
@router.get(r"/tiles/{z}/{x}/{y}\.{ext}", **params)
@router.get(r"/tiles/{z}/{x}/{y}@{scale}x", **params)
@router.get(r"/tiles/{z}/{x}/{y}@{scale}x\.{ext}", **params)
@router.get(r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}", **params)
@router.get(r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}\.{ext}", **params)
@router.get(r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x", **params)
@router.get(r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x\.{ext}", **params)
async def cog_tile(
    z: int = Path(..., ge=0, le=30, description="Mercator tiles's zoom level"),
    x: int = Path(..., description="Mercator tiles's column"),
    y: int = Path(..., description="Mercator tiles's row"),
    TileMatrixSetId: TileMatrixSetNames = Query(
        TileMatrixSetNames.WebMercatorQuad,  # type: ignore
        description="TileMatrixSet Name (default: 'WebMercatorQuad')",
    ),
    scale: int = Query(
        1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
    ),
    ext: ImageType = Query(None, description="Output image type. Default is auto."),
    url: str = Query(..., description="Cloud Optimized GeoTIFF URL."),
    image_params: CommonImageParams = Depends(CommonImageParams),
    cache_client: CacheLayer = Depends(utils.get_cache),
):
    """Create map tile from a COG."""
    timings = []
    headers: Dict[str, str] = {}

    tile_hash = utils.get_hash(
        **dict(
            identifier=TileMatrixSetId.name,
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
    tms = morecantile.tms.get(TileMatrixSetId.name)

    content = None
    if cache_client:
        try:
            content, ext = cache_client.get_image_from_cache(tile_hash)
            headers["X-Cache"] = "HIT"
        except Exception:
            content = None

    if not content:
        with utils.Timer() as t:
            with COGReader(url, tms=tms) as cog:
                tile, mask = cog.tile(
                    x,
                    y,
                    z,
                    tilesize=tilesize,
                    indexes=image_params.indexes,
                    expression=image_params.expression,
                    nodata=image_params.nodata,
                )
                colormap = image_params.color_map or cog.colormap

        timings.append(("Read", t.elapsed))

        if not ext:
            ext = ImageType.jpg if mask.all() else ImageType.png

        with utils.Timer() as t:
            tile = utils.postprocess(
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
                    bounds = tms.xy_bounds(x, y, z)
                    dst_transform = from_bounds(*bounds, tilesize, tilesize)
                    options = {"crs": tms.crs, "transform": dst_transform}
                content = render(
                    tile, mask, img_format=driver, colormap=colormap, **options
                )
        timings.append(("Format", t.elapsed))

        if cache_client and content:
            cache_client.set_image_cache(tile_hash, (content, ext))

    if timings:
        headers["X-Server-Timings"] = "; ".join(
            ["{} - {:0.2f}".format(name, time * 1000) for (name, time) in timings]
        )

    return TileResponse(
        content, media_type=ImageMimeTypes[ext.value].value, headers=headers,
    )


@router.get(
    "/tilejson.json",
    response_model=TileJSON,
    responses={200: {"description": "Return a tilejson"}},
    response_model_exclude_none=True,
)
@router.get(
    "/{TileMatrixSetId}/tilejson.json",
    response_model=TileJSON,
    responses={200: {"description": "Return a tilejson"}},
    response_model_exclude_none=True,
)
async def cog_tilejson(
    request: Request,
    response: Response,
    TileMatrixSetId: TileMatrixSetNames = Query(
        TileMatrixSetNames.WebMercatorQuad,  # type: ignore
        description="TileMatrixSet Name (default: 'WebMercatorQuad')",
    ),
    url: str = Query(..., description="Cloud Optimized GeoTIFF URL."),
    tile_format: Optional[ImageType] = Query(
        None, description="Output image type. Default is auto."
    ),
    tile_scale: int = Query(
        1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
    ),
    minzoom: Optional[int] = Query(None, description="Overwrite default minzoom."),
    maxzoom: Optional[int] = Query(None, description="Overwrite default maxzoom."),
):
    """Return TileJSON document for a COG."""
    scheme = request.url.scheme
    host = request.headers["host"]

    kwargs = dict(request.query_params)
    kwargs.pop("tile_format", None)
    kwargs.pop("tile_scale", None)
    kwargs.pop("TileMatrixSetId", None)

    qs = urlencode(list(kwargs.items()))
    if tile_format:
        tile_url = f"{scheme}://{host}/cog/tiles/{TileMatrixSetId.name}/{{z}}/{{x}}/{{y}}@{tile_scale}x.{tile_format}?{qs}"
    else:
        tile_url = f"{scheme}://{host}/cog/tiles/{TileMatrixSetId.name}/{{z}}/{{x}}/{{y}}@{tile_scale}x?{qs}"

    tms = morecantile.tms.get(TileMatrixSetId.name)
    with COGReader(url, tms=tms) as cog:
        center = list(cog.center)
        if minzoom:
            center[-1] = minzoom
        tjson = {
            "bounds": cog.bounds,
            "center": tuple(center),
            "minzoom": minzoom or cog.minzoom,
            "maxzoom": maxzoom or cog.maxzoom,
            "name": os.path.basename(url),
            "tiles": [tile_url],
        }

    response.headers["Cache-Control"] = "max-age=3600"
    return tjson


@router.get("/WMTSCapabilities.xml", response_class=XMLResponse, tags=["OGC"])
@router.get(
    "/{TileMatrixSetId}/WMTSCapabilities.xml", response_class=XMLResponse, tags=["OGC"],
)
def wtms(
    request: Request,
    response: Response,
    TileMatrixSetId: TileMatrixSetNames = Query(
        TileMatrixSetNames.WebMercatorQuad,  # type: ignore
        description="TileMatrixSet Name (default: 'WebMercatorQuad')",
    ),
    url: str = Query(..., description="Cloud Optimized GeoTIFF URL."),
    tile_format: ImageType = Query(
        ImageType.png, description="Output image type. Default is png."
    ),
    tile_scale: int = Query(
        1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
    ),
):
    """OGC WMTS endpoit."""
    scheme = request.url.scheme
    host = request.headers["host"]
    endpoint = f"{scheme}://{host}/cog"

    kwargs = dict(request.query_params)
    kwargs.pop("tile_format", None)
    kwargs.pop("tile_scale", None)
    qs = urlencode(list(kwargs.items()))

    tms = morecantile.tms.get(TileMatrixSetId.name)
    with COGReader(url, tms=tms) as cog:
        minzoom, maxzoom, bounds = cog.minzoom, cog.maxzoom, cog.bounds

    media_type = ImageMimeTypes[tile_format.value].value

    tileMatrix = []
    for zoom in range(minzoom, maxzoom + 1):
        matrix = tms.matrix(zoom)
        tm = f"""
                <TileMatrix>
                    <ows:Identifier>{matrix.identifier}</ows:Identifier>
                    <ScaleDenominator>{matrix.scaleDenominator}</ScaleDenominator>
                    <TopLeftCorner>{matrix.topLeftCorner[0]} {matrix.topLeftCorner[1]}</TopLeftCorner>
                    <TileWidth>{matrix.tileWidth}</TileWidth>
                    <TileHeight>{matrix.tileHeight}</TileHeight>
                    <MatrixWidth>{matrix.matrixWidth}</MatrixWidth>
                    <MatrixHeight>{matrix.matrixHeight}</MatrixHeight>
                </TileMatrix>"""
        tileMatrix.append(tm)

    tile_ext = f"@{tile_scale}x.{tile_format.value}"
    return templates.TemplateResponse(
        "wmts.xml",
        {
            "request": request,
            "endpoint": endpoint,
            "bounds": bounds,
            "tileMatrix": tileMatrix,
            "tms": tms,
            "title": "Cloud Optimized GeoTIFF",
            "query_string": qs,
            "tile_format": tile_ext,
            "media_type": media_type,
        },
        media_type=MimeTypes.xml.value,
    )


@router.get("/viewer", response_class=HTMLResponse, tags=["Webpage"])
def cog_viewer(request: Request, template=Depends(web_template)):
    """Cloud Optimized GeoTIFF Viewer."""
    return template(request, "cog_index.html", "cog_tilejson", "cog_metadata")
