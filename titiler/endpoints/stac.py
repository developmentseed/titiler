"""API for SpatioTemporal Asset Catalog items."""

import os
import re
from typing import Dict, List, Optional, Union
from urllib.parse import urlencode

from rasterio.transform import from_bounds
from rio_tiler.errors import MissingAssets
from rio_tiler_crs import STACReader

from titiler import utils
from titiler.db.memcache import CacheLayer
from titiler.dependencies import (
    CommonImageParams,
    CommonMetadataParams,
    CommonTileParams,
    TileMatrixSetNames,
    morecantile,
    request_hash,
)
from titiler.models.cog import cogBounds, cogInfo, cogMetadata
from titiler.models.mapbox import TileJSON
from titiler.ressources.common import img_endpoint_params
from titiler.ressources.enums import ImageMimeTypes, ImageType, MimeTypes
from titiler.ressources.responses import XMLResponse

from fastapi import APIRouter, Depends, Path, Query

from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="titiler/templates")


@router.get(
    "/bounds",
    response_model=cogBounds,
    responses={200: {"description": "Return the bounds of the STAC item."}},
)
async def stac_bounds(url: str = Query(..., description="STAC item URL.")):
    """Return the bounds of the STAC item."""
    with STACReader(url) as stac:
        return {"bounds": stac.bounds}


@router.get(
    "/info",
    response_model=Union[List[str], Dict[str, cogInfo]],
    response_model_exclude={"__all__": {"minzoom", "maxzoom", "center"}},
    response_model_exclude_none=True,
    responses={200: {"description": "Return basic info for STAC item's assets"}},
)
async def stac_info(
    url: str = Query(..., description="STAC item URL."),
    assets: str = Query(None, description="comma (,) separated list of asset names."),
):
    """Return basic info on STAC item's COG."""
    with STACReader(url) as stac:
        if not assets:
            return stac.assets

        info = stac.info(assets=assets.split(","))

    return info


@router.get(
    "/metadata",
    response_model=Dict[str, cogMetadata],
    response_model_exclude={"__all__": {"minzoom", "maxzoom", "center"}},
    response_model_exclude_none=True,
    responses={200: {"description": "Return the metadata for STAC item's assets."}},
)
async def stac_metadata(
    request: Request,
    url: str = Query(..., description="STAC item URL."),
    assets: str = Query(..., description="comma (,) separated list of asset names."),
    metadata_params: CommonMetadataParams = Depends(),
):
    """Return the metadata of the COG."""
    with STACReader(url) as stac:
        info = stac.metadata(
            metadata_params.pmin,
            metadata_params.pmax,
            assets=assets.split(","),
            nodata=metadata_params.nodata,
            indexes=metadata_params.indexes,
            max_size=metadata_params.max_size,
            hist_options=metadata_params.hist_options,
            bounds=metadata_params.bounds,
            **metadata_params.kwargs,
        )
    return info


@router.get(r"/tiles/{z}/{x}/{y}", **img_endpoint_params)
@router.get(r"/tiles/{z}/{x}/{y}.{format}", **img_endpoint_params)
@router.get(r"/tiles/{z}/{x}/{y}@{scale}x", **img_endpoint_params)
@router.get(r"/tiles/{z}/{x}/{y}@{scale}x.{format}", **img_endpoint_params)
@router.get(r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}", **img_endpoint_params)
@router.get(r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}.{format}", **img_endpoint_params)
@router.get(r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x", **img_endpoint_params)
@router.get(
    r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}", **img_endpoint_params
)
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
    format: ImageType = Query(None, description="Output image type. Default is auto."),
    url: str = Query(..., description="STAC Item URL."),
    assets: str = Query("", description="comma (,) separated list of asset names."),
    image_params: CommonTileParams = Depends(),
    cache_client: CacheLayer = Depends(utils.get_cache),
    request_id: str = Depends(request_hash),
):
    """Create map tile from a STAC item."""
    timings = []
    headers: Dict[str, str] = {}

    tilesize = scale * 256
    tms = morecantile.tms.get(TileMatrixSetId.name)

    content = None
    if cache_client:
        try:
            content, ext = cache_client.get_image_from_cache(request_id)
            format = ImageType[ext]
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

        if not format:
            format = ImageType.jpg if mask.all() else ImageType.png

        with utils.Timer() as t:
            tile = utils.postprocess(
                tile,
                mask,
                rescale=image_params.rescale,
                color_formula=image_params.color_formula,
            )
        timings.append(("Post-process", t.elapsed))

        bounds = tms.xy_bounds(x, y, z)
        dst_transform = from_bounds(*bounds, tilesize, tilesize)
        with utils.Timer() as t:
            content = utils.reformat(
                tile,
                mask,
                format,
                colormap=image_params.color_map,
                transform=dst_transform,
                crs=tms.crs,
            )
        timings.append(("Format", t.elapsed))

        if cache_client and content:
            cache_client.set_image_cache(request_id, (content, format.value))

    if timings:
        headers["X-Server-Timings"] = "; ".join(
            ["{} - {:0.2f}".format(name, time * 1000) for (name, time) in timings]
        )

    return Response(
        content, media_type=ImageMimeTypes[format.value].value, headers=headers,
    )


@router.get(r"/preview", **img_endpoint_params)
@router.get(r"/preview.{format}", **img_endpoint_params)
async def stac_preview(
    format: ImageType = Query(None, description="Output image type. Default is auto."),
    url: str = Query(..., description="STAC Item URL."),
    assets: str = Query("", description="comma (,) separated list of asset names."),
    image_params: CommonImageParams = Depends(),
):
    """Create preview of STAC assets."""
    timings = []
    headers: Dict[str, str] = {}

    with utils.Timer() as t:
        with STACReader(url) as stac:
            data, mask = stac.preview(
                assets=assets.split(","),
                expression=image_params.expression,
                height=image_params.height,
                width=image_params.width,
                max_size=image_params.max_size,
                indexes=image_params.indexes,
                nodata=image_params.nodata,
                **image_params.kwargs,
            )
    timings.append(("Read", t.elapsed))

    if not format:
        format = ImageType.jpg if mask.all() else ImageType.png

    with utils.Timer() as t:
        data = utils.postprocess(
            data,
            mask,
            rescale=image_params.rescale,
            color_formula=image_params.color_formula,
        )
    timings.append(("Post-process", t.elapsed))

    with utils.Timer() as t:
        content = utils.reformat(data, mask, format, colormap=image_params.color_map)
    timings.append(("Format", t.elapsed))

    if timings:
        headers["X-Server-Timings"] = "; ".join(
            ["{} - {:0.2f}".format(name, time * 1000) for (name, time) in timings]
        )

    return Response(
        content, media_type=ImageMimeTypes[format.value].value, headers=headers,
    )


# @router.get(r"/crop/{minx},{miny},{maxx},{maxy}", **img_endpoint_params)
@router.get(r"/crop/{minx},{miny},{maxx},{maxy}.{format}", **img_endpoint_params)
async def stac_part(
    minx: float = Path(..., description="Bounding box min X"),
    miny: float = Path(..., description="Bounding box min Y"),
    maxx: float = Path(..., description="Bounding box max X"),
    maxy: float = Path(..., description="Bounding box max Y"),
    format: ImageType = Query(None, description="Output image type."),
    url: str = Query(..., description="STAC Item URL."),
    assets: str = Query("", description="comma (,) separated list of asset names."),
    image_params: CommonImageParams = Depends(),
):
    """Create image from part of STAC assets."""
    timings = []
    headers: Dict[str, str] = {}

    with utils.Timer() as t:
        with STACReader(url) as stac:
            data, mask = stac.part(
                [minx, miny, maxx, maxy],
                height=image_params.height,
                width=image_params.width,
                max_size=image_params.max_size,
                assets=assets.split(","),
                expression=image_params.expression,
                indexes=image_params.indexes,
                nodata=image_params.nodata,
                **image_params.kwargs,
            )
    timings.append(("Read", t.elapsed))

    with utils.Timer() as t:
        data = utils.postprocess(
            data,
            mask,
            rescale=image_params.rescale,
            color_formula=image_params.color_formula,
        )
    timings.append(("Post-process", t.elapsed))

    with utils.Timer() as t:
        content = utils.reformat(data, mask, format, colormap=image_params.color_map)
    timings.append(("Format", t.elapsed))

    if timings:
        headers["X-Server-Timings"] = "; ".join(
            ["{} - {:0.2f}".format(name, time * 1000) for (name, time) in timings]
        )

    return Response(
        content, media_type=ImageMimeTypes[format.value].value, headers=headers,
    )


@router.get(
    r"/point/{lon},{lat}",
    responses={200: {"description": "Return a value for a point"}},
)
async def cog_point(
    lon: float = Path(..., description="Longitude"),
    lat: float = Path(..., description="Latitude"),
    url: str = Query(..., description="Cloud Optimized GeoTIFF URL."),
    assets: str = Query("", description="comma (,) separated list of asset names."),
    expression: Optional[str] = Query(
        None,
        title="Band Math expression",
        description="rio-tiler's band math expression (e.g B1/B2)",
    ),
    bidx: Optional[str] = Query(
        None, title="Band indexes", description="comma (',') delimited band indexes",
    ),
    asset_expression: Optional[str] = Query(
        None,
        title="Band Math expression for assets bands",
        description="rio-tiler's band math expression (e.g B1/B2)",
    ),
):
    """Get Point value for a COG."""

    indexes = tuple(int(s) for s in re.findall(r"\d+", bidx)) if bidx else None

    timings = []
    headers: Dict[str, str] = {}

    with utils.Timer() as t:
        with STACReader(url) as stac:
            values = stac.point(
                lon,
                lat,
                assets=assets,
                expression=expression,
                indexes=indexes,
                asset_expression=asset_expression,
            )
    timings.append(("Read", t.elapsed))

    if timings:
        headers["X-Server-Timings"] = "; ".join(
            ["{} - {:0.2f}".format(name, time * 1000) for (name, time) in timings]
        )

    return {"coordinates": [lon, lat], "values": values}


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
async def stac_tilejson(
    request: Request,
    TileMatrixSetId: TileMatrixSetNames = Query(
        TileMatrixSetNames.WebMercatorQuad,  # type: ignore
        description="TileMatrixSet Name (default: 'WebMercatorQuad')",
    ),
    url: str = Query(..., description="STAC Item URL."),
    assets: str = Query("", description="comma (,) separated list of asset names."),
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
    if not expression and not assets:
        raise MissingAssets("Expression or Assets HAVE to be set in the queryString.")

    kwargs = {
        "z": "{z}",
        "x": "{x}",
        "y": "{y}",
        "scale": tile_scale,
        "TileMatrixSetId": TileMatrixSetId.name,
    }
    if tile_format:
        kwargs["format"] = tile_format.value

    q = dict(request.query_params)
    q.pop("tile_format", None)
    q.pop("tile_scale", None)
    q.pop("TileMatrixSetId", None)
    q.pop("minzoom", None)
    q.pop("maxzoom", None)
    qs = urlencode(list(q.items()))

    tiles_url = request.url_for("stac_tile", **kwargs).replace("\\", "")
    tiles_url += f"?{qs}"

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
            "tiles": [tiles_url],
        }

    return tjson


@router.get("/WMTSCapabilities.xml", response_class=XMLResponse, tags=["OGC"])
@router.get(
    "/{TileMatrixSetId}/WMTSCapabilities.xml", response_class=XMLResponse, tags=["OGC"],
)
def stac_wmts(
    request: Request,
    TileMatrixSetId: TileMatrixSetNames = Query(
        TileMatrixSetNames.WebMercatorQuad,  # type: ignore
        description="TileMatrixSet Name (default: 'WebMercatorQuad')",
    ),
    url: str = Query(..., description="STAC Item URL."),
    assets: str = Query("", description="comma (,) separated list of asset names."),
    expression: Optional[str] = Query(
        None,
        title="Band Math expression",
        description="rio-tiler's band math expression (e.g B1/B2)",
    ),
    tile_format: ImageType = Query(
        ImageType.png, description="Output image type. Default is png."
    ),
    tile_scale: int = Query(
        1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
    ),
    minzoom: Optional[int] = Query(None, description="Overwrite default minzoom."),
    maxzoom: Optional[int] = Query(None, description="Overwrite default maxzoom."),
):
    """OGC WMTS endpoint."""
    if not expression and not assets:
        raise MissingAssets("Expression or Assets HAVE to be set in the queryString.")

    kwargs = {
        "z": "{TileMatrix}",
        "x": "{TileCol}",
        "y": "{TileRow}",
        "scale": tile_scale,
        "format": tile_format.value,
        "TileMatrixSetId": TileMatrixSetId.name,
    }
    tiles_endpoint = request.url_for("stac_tile", **kwargs)
    q = dict(request.query_params)
    q.pop("TileMatrixSetId", None)
    q.pop("tile_format", None)
    q.pop("tile_scale", None)
    q.pop("minzoom", None)
    q.pop("maxzoom", None)
    q.pop("SERVICE", None)
    q.pop("REQUEST", None)
    qs = urlencode(list(q.items()))
    tiles_endpoint += f"?{qs}"

    tms = morecantile.tms.get(TileMatrixSetId.name)
    with STACReader(url, tms=tms) as stac:
        bounds = stac.bounds
        center = list(stac.center)
        if minzoom:
            center[-1] = minzoom
        minzoom = minzoom or stac.minzoom
        maxzoom = maxzoom or stac.maxzoom

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

    return templates.TemplateResponse(
        "wmts.xml",
        {
            "request": request,
            "tiles_endpoint": tiles_endpoint,
            "bounds": bounds,
            "tileMatrix": tileMatrix,
            "tms": tms,
            "title": "Spatial Temporal Catalog",
            "layer_name": "stac",
            "media_type": media_type,
        },
        media_type=MimeTypes.xml.value,
    )
