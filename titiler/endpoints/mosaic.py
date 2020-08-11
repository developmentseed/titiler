"""API for MosaicJSON Dataset."""

import os
import re
from typing import Dict, Optional
from urllib.parse import urlencode

import morecantile
from cogeo_mosaic.backends import MosaicBackend
from cogeo_mosaic.mosaic import MosaicJSON
from cogeo_mosaic.utils import get_footprints
from rio_tiler.constants import MAX_THREADS
from rio_tiler_crs.cogeo import geotiff_options

from titiler import utils
from titiler.dependencies import CommonTileParams, MosaicPath
from titiler.errors import BadRequestError, TileNotFoundError
from titiler.models.cog import cogBounds
from titiler.models.mapbox import TileJSON
from titiler.models.mosaic import CreateMosaicJSON, UpdateMosaicJSON, mosaicInfo
from titiler.ressources.common import img_endpoint_params
from titiler.ressources.enums import (
    ImageMimeTypes,
    ImageType,
    MimeTypes,
    PixelSelectionMethod,
)
from titiler.ressources.responses import XMLResponse

from fastapi import APIRouter, Depends, Path, Query

from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="titiler/templates")


@router.post("", response_model=MosaicJSON, response_model_exclude_none=True)
def create_mosaicjson(body: CreateMosaicJSON):
    """Create a MosaicJSON"""
    mosaic = MosaicJSON.from_urls(
        body.files,
        minzoom=body.minzoom,
        maxzoom=body.maxzoom,
        max_threads=body.max_threads,
    )
    mosaic_path = MosaicPath(body.url)
    with MosaicBackend(mosaic_path, mosaic_def=mosaic) as mosaic:
        try:
            mosaic.write()
        except NotImplementedError:
            raise BadRequestError(
                f"{mosaic.__class__.__name__} does not support write operations"
            )
        return mosaic.mosaic_def


@router.get(
    "",
    response_model=MosaicJSON,
    response_model_exclude_none=True,
    responses={200: {"description": "Return MosaicJSON definition"}},
)
def read_mosaicjson(mosaic_path: str = Depends(MosaicPath)):
    """Read a MosaicJSON"""
    with MosaicBackend(mosaic_path) as mosaic:
        return mosaic.mosaic_def


@router.put("", response_model=MosaicJSON, response_model_exclude_none=True)
def update_mosaicjson(body: UpdateMosaicJSON):
    """Update an existing MosaicJSON"""
    mosaic_path = MosaicPath(body.url)
    with MosaicBackend(mosaic_path) as mosaic:
        features = get_footprints(body.files, max_threads=body.max_threads)
        try:
            mosaic.update(features, add_first=body.add_first, quiet=True)
        except NotImplementedError:
            raise BadRequestError(
                f"{mosaic.__class__.__name__} does not support update operations"
            )
        return mosaic.mosaic_def


@router.get(
    "/bounds",
    response_model=cogBounds,
    responses={200: {"description": "Return the bounds of the MosaicJSON"}},
)
def mosaicjson_bounds(mosaic_path: str = Depends(MosaicPath)):
    """Read MosaicJSON bounds"""
    with MosaicBackend(mosaic_path) as mosaic:
        return {"bounds": mosaic.mosaic_def.bounds}


@router.get("/info", response_model=mosaicInfo)
def mosaicjson_info(mosaic_path: str = Depends(MosaicPath)):
    """
    Read MosaicJSON info

    Ref: https://github.com/developmentseed/cogeo-mosaic-tiler/blob/master/cogeo_mosaic_tiler/handlers/app.py#L164-L198
    """
    with MosaicBackend(mosaic_path) as mosaic:
        meta = mosaic.metadata
        response = {
            "bounds": meta["bounds"],
            "center": meta["center"],
            "maxzoom": meta["maxzoom"],
            "minzoom": meta["minzoom"],
            "name": mosaic_path,
            "quadkeys": list(mosaic.mosaic_def.tiles),
        }
        return response


@router.get(r"/tiles/{z}/{x}/{y}", **img_endpoint_params)
@router.get(r"/tiles/{z}/{x}/{y}.{format}", **img_endpoint_params)
@router.get(r"/tiles/{z}/{x}/{y}@{scale}x", **img_endpoint_params)
@router.get(r"/tiles/{z}/{x}/{y}@{scale}x.{format}", **img_endpoint_params)
@router.get(r"/tiles/WebMercatorQuad/{z}/{x}/{y}.{format}", **img_endpoint_params)
@router.get(r"/tiles/WebMercatorQuad/{z}/{x}/{y}@{scale}x", **img_endpoint_params)
@router.get(
    r"/tiles/WebMercatorQuad/{z}/{x}/{y}@{scale}x.{format}", **img_endpoint_params
)
async def mosaic_tile(
    z: int = Path(..., ge=0, le=30, description="Mercator tiles's zoom level"),
    x: int = Path(..., description="Mercator tiles's column"),
    y: int = Path(..., description="Mercator tiles's row"),
    scale: int = Query(
        1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
    ),
    format: ImageType = Query(None, description="Output image type. Default is auto."),
    pixel_selection: PixelSelectionMethod = Query(
        PixelSelectionMethod.first, description="Pixel selection method."
    ),
    image_params: CommonTileParams = Depends(),
    mosaic_path: str = Depends(MosaicPath),
):
    """Read MosaicJSON tile"""
    timings = []
    headers: Dict[str, str] = {}

    tilesize = 256 * scale
    threads = int(os.getenv("MOSAIC_CONCURRENCY", MAX_THREADS))

    with utils.Timer() as t:
        with MosaicBackend(mosaic_path) as mosaic:
            (tile, mask), assets_used = mosaic.tile(
                x,
                y,
                z,
                pixel_selection=pixel_selection.method(),
                threads=threads,
                tilesize=tilesize,
                indexes=image_params.indexes,
                expression=image_params.expression,
                nodata=image_params.nodata,
                **image_params.kwargs,
            )

    timings.append(("Read-tile", t.elapsed))

    if tile is None:
        raise TileNotFoundError(f"Tile {z}/{x}/{y} was not found")

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

    opts = {}
    if ImageType.tif in format:
        opts = geotiff_options(x, y, z, tilesize=tilesize)

    with utils.Timer() as t:
        content = utils.reformat(
            tile, mask, format, colormap=image_params.color_map, **opts
        )
    timings.append(("Format", t.elapsed))

    if timings:
        headers["X-Server-Timings"] = "; ".join(
            ["{} - {:0.2f}".format(name, time * 1000) for (name, time) in timings]
        )

    if assets_used:
        headers["X-Assets"] = ",".join(assets_used)

    return Response(
        content, media_type=ImageMimeTypes[format.value].value, headers=headers
    )


@router.get(
    r"/point/{lon},{lat}",
    responses={200: {"description": "Return a value for a point"}},
)
async def mosaic_point(
    lon: float = Path(..., description="Longitude"),
    lat: float = Path(..., description="Latitude"),
    bidx: Optional[str] = Query(
        None, title="Band indexes", description="comma (',') delimited band indexes",
    ),
    expression: Optional[str] = Query(
        None,
        title="Band Math expression",
        description="rio-tiler's band math expression (e.g B1/B2)",
    ),
    mosaic_path: str = Depends(MosaicPath),
):
    """Get Point value for a MosaicJSON."""
    indexes = tuple(int(s) for s in re.findall(r"\d+", bidx)) if bidx else None

    timings = []
    headers: Dict[str, str] = {}
    threads = int(os.getenv("MOSAIC_CONCURRENCY", MAX_THREADS))

    with utils.Timer() as t:
        with MosaicBackend(mosaic_path) as mosaic:
            values = mosaic.point(lon, lat, indexes=indexes, threads=threads)

    timings.append(("Read-values", t.elapsed))

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
def mosaic_tilejson(
    request: Request,
    tile_scale: int = Query(
        1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
    ),
    tile_format: Optional[ImageType] = Query(
        None, description="Output image type. Default is auto."
    ),
    minzoom: Optional[int] = Query(None, description="Overwrite default minzoom."),
    maxzoom: Optional[int] = Query(None, description="Overwrite default maxzoom."),
    mosaic_path: str = Depends(MosaicPath),
):
    """Create TileJSON"""
    kwargs = {"z": "{z}", "x": "{x}", "y": "{y}", "scale": tile_scale}
    if tile_format:
        kwargs["format"] = tile_format
    tiles_url = request.url_for("mosaic_tile", **kwargs).replace("\\", "")

    q = dict(request.query_params)
    q.pop("tile_format", None)
    q.pop("tile_scale", None)
    q.pop("minzoom", None)
    q.pop("maxzoom", None)
    qs = urlencode(list(q.items()))
    tiles_url += f"?{qs}"

    with MosaicBackend(mosaic_path) as mosaic:
        tjson = TileJSON(**mosaic.metadata, tiles=[tiles_url])

    return tjson


@router.get("/WMTSCapabilities.xml", response_class=XMLResponse, tags=["OGC"])
def mosaic_wmts(
    request: Request,
    tile_format: ImageType = Query(
        ImageType.png, description="Output image type. Default is png."
    ),
    tile_scale: int = Query(
        1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
    ),
    minzoom: Optional[int] = Query(None, description="Overwrite default minzoom."),
    maxzoom: Optional[int] = Query(None, description="Overwrite default maxzoom."),
    mosaic_path: str = Depends(MosaicPath),
):
    """OGC WMTS endpoint."""
    kwargs = {
        "z": "{TileMatrix}",
        "x": "{TileCol}",
        "y": "{TileRow}",
        "scale": tile_scale,
        "format": tile_format.value,
    }
    tiles_endpoint = request.url_for("mosaic_tile", **kwargs)

    q = dict(request.query_params)
    q.pop("tile_format", None)
    q.pop("tile_scale", None)
    q.pop("minzoom", None)
    q.pop("maxzoom", None)
    q.pop("SERVICE", None)
    q.pop("REQUEST", None)
    qs = urlencode(list(q.items()))
    tiles_endpoint += f"?{qs}"

    tms = morecantile.tms.get("WebMercatorQuad")
    with MosaicBackend(mosaic_path) as mosaic:
        minzoom = minzoom or mosaic.mosaic_def.minzoom
        maxzoom = maxzoom or mosaic.mosaic_def.maxzoom
        bounds = mosaic.mosaic_def.bounds

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
            "title": "Cloud Optimized GeoTIFF",
            "layer_name": "Mosaic",
            "media_type": media_type,
        },
        media_type=MimeTypes.xml.value,
    )
