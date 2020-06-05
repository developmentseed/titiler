"""API tiles."""

from typing import Any, Dict, Optional

import json
import os
from io import BytesIO
from urllib.parse import urlencode

import numpy

from fastapi import APIRouter, Depends, Query, Path, HTTPException
from starlette import status
from starlette.requests import Request
from starlette.responses import Response

from morecantile.models import TileMatrixSet

from rasterio.transform import from_bounds
from rio_tiler_crs import COGReader
from rio_tiler.utils import render
from rio_tiler.profiles import img_profiles
from stac_tiler import STACReader

from titiler.api import utils
from titiler.api.deps import CommonImageParams, TileMatrixSetNames, morecantile
from titiler.db.memcache import CacheLayer
from titiler.ressources.enums import ImageType, ImageMimeTypes
from titiler.ressources.common import drivers
from titiler.ressources.responses import TileResponse
from titiler.models.OGC import TileMatrixSetList
from titiler.core import config
from titiler.models.mapbox import TileJSON


router = APIRouter()


@router.get(
    r"/tileMatrixSets",
    response_model=TileMatrixSetList,
    response_model_exclude_none=True,
    tags=["TileMatrixSets"],
)
async def tms_list(request: Request):
    """
    Return list of supported TileMatrixSets.

    Specs: http://docs.opengeospatial.org/per/19-069.html#_tilematrixsets
    """
    scheme = request.url.scheme
    host = request.headers["host"]
    if config.API_VERSION_STR:
        host += config.API_VERSION_STR

    tms_list = morecantile.tms.list()
    return {
        "tileMatrixSets": [
            {
                "id": tms,
                "title": morecantile.tms.get(tms).title,
                "links": [
                    {
                        "href": f"{scheme}://{host}/tileMatrixSets/{tms}",
                        "rel": "item",
                        "type": "application/json",
                    }
                ],
            }
            for tms in tms_list
        ]
    }


@router.get(
    r"/tileMatrixSets/{TileMatrixSetId}",
    response_model=TileMatrixSet,
    response_model_exclude_none=True,
    tags=["TileMatrixSets"],
)
async def tms_info(
    TileMatrixSetId: TileMatrixSetNames = Query(..., description="TileMatrixSet Name")
):
    """Return TileMatrixSet JSON document."""
    tms = morecantile.tms.get(TileMatrixSetId.name)
    return json.loads(tms.json(exclude_none=True))


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
    "tags": ["COG"],
}


@router.get(r"/cog/tiles/{z}/{x}/{y}", **params)
@router.get(r"/cog/tiles/{z}/{x}/{y}\.{ext}", **params)
@router.get(r"/cog/tiles/{z}/{x}/{y}@{scale}x", **params)
@router.get(r"/cog/tiles/{z}/{x}/{y}@{scale}x\.{ext}", **params)
@router.get(r"/cog/tiles/{TileMatrixSetId}/{z}/{x}/{y}", **params)
@router.get(r"/cog/tiles/{TileMatrixSetId}/{z}/{x}/{y}\.{ext}", **params)
@router.get(r"/cog/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x", **params)
@router.get(r"/cog/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x\.{ext}", **params)
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
    "/cog/tilejson.json",
    response_model=TileJSON,
    responses={200: {"description": "Return a tilejson"}},
    response_model_exclude_none=True,
    tags=["COG"],
)
@router.get(
    "/cog/{TileMatrixSetId}/tilejson.json",
    response_model=TileJSON,
    responses={200: {"description": "Return a tilejson"}},
    response_model_exclude_none=True,
    tags=["COG"],
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
    if config.API_VERSION_STR:
        host += config.API_VERSION_STR

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


params["tags"] = ["STAC"]


@router.get(r"/stac/tiles/{z}/{x}/{y}", **params)
@router.get(r"/stac/tiles/{z}/{x}/{y}\.{ext}", **params)
@router.get(r"/stac/tiles/{z}/{x}/{y}@{scale}x", **params)
@router.get(r"/stac/tiles/{z}/{x}/{y}@{scale}x\.{ext}", **params)
@router.get(r"/stac/tiles/{TileMatrixSetId}/{z}/{x}/{y}", **params)
@router.get(r"/stac/tiles/{TileMatrixSetId}/{z}/{x}/{y}\.{ext}", **params)
@router.get(r"/stac/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x", **params)
@router.get(r"/stac/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x\.{ext}", **params)
async def stac_tile(
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
    url: str = Query(..., description="STAC Item URL."),
    assets: str = Query("", description="Comma (,) separated list of asset names."),
    image_params: CommonImageParams = Depends(CommonImageParams),
    cache_client: CacheLayer = Depends(utils.get_cache),
):
    """Create map tile from a STAC item."""
    timings = []
    headers: Dict[str, str] = {}

    if not image_params.expression and not assets:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must pass Expression or Asset list.",
        )

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
            with STACReader(url, tms=tms) as stac:
                tile, mask = stac.tile(
                    x,
                    y,
                    z,
                    assets=assets.split(","),
                    tilesize=tilesize,
                    indexes=image_params.indexes,
                    expression=image_params.expression,
                    nodata=image_params.nodata,
                )
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
                    tile,
                    mask,
                    img_format=driver,
                    colormap=image_params.color_map,
                    **options,
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
    "/stac/tilejson.json",
    response_model=TileJSON,
    responses={200: {"description": "Return a tilejson"}},
    response_model_exclude_none=True,
    tags=["STAC"],
)
@router.get(
    "/stac/{TileMatrixSetId}/tilejson.json",
    response_model=TileJSON,
    responses={200: {"description": "Return a tilejson"}},
    response_model_exclude_none=True,
    tags=["STAC"],
)
async def stac_tilejson(
    request: Request,
    response: Response,
    TileMatrixSetId: TileMatrixSetNames = Query(
        TileMatrixSetNames.WebMercatorQuad,  # type: ignore
        description="TileMatrixSet Name (default: 'WebMercatorQuad')",
    ),
    url: str = Query(..., description="STAC Item URL."),
    assets: str = Query("", description="Comma (,) separated list of asset names."),
    expression: Optional[str] = Query(
        None,
        title="Band Math expression",
        description="rio-tiler's band math expression (e.g B1/B2)",
    ),
    tile_format: Optional[ImageType] = Query(
        None, description="Output image type. Default is auto."
    ),
    tile_scale: int = Query(
        1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
    ),
    minzoom: Optional[int] = Query(None, description="Overwrite default minzoom."),
    maxzoom: Optional[int] = Query(None, description="Overwrite default maxzoom."),
):
    """Return a TileJSON document for a STAC item."""
    scheme = request.url.scheme
    host = request.headers["host"]
    if config.API_VERSION_STR:
        host += config.API_VERSION_STR

    kwargs = dict(request.query_params)
    kwargs.pop("tile_format", None)
    kwargs.pop("tile_scale", None)
    kwargs.pop("TileMatrixSetId", None)

    if not expression and not assets:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Expression or Assets HAVE to be set in the queryString.",
        )

    qs = urlencode(list(kwargs.items()))
    if tile_format:
        tile_url = f"{scheme}://{host}/stac/tiles/{TileMatrixSetId.name}/{{z}}/{{x}}/{{y}}@{tile_scale}x.{tile_format}?{qs}"
    else:
        tile_url = f"{scheme}://{host}/stac/tiles/{TileMatrixSetId.name}/{{z}}/{{x}}/{{y}}@{tile_scale}x?{qs}"

    tms = morecantile.tms.get(TileMatrixSetId.name)
    with STACReader(url, tms=tms) as stac:
        center = list(stac.center)
        if minzoom:
            center[-1] = minzoom
        tjson = {
            "bounds": stac.bounds,
            "center": tuple(center),
            "minzoom": minzoom or stac.minzoom,
            "maxzoom": maxzoom or stac.maxzoom,
            "name": os.path.basename(url),
            "tiles": [tile_url],
        }

    response.headers["Cache-Control"] = "max-age=3600"
    return tjson
