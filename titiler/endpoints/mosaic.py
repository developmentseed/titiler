"""API for MosaicJSON Dataset."""

import asyncio
import os
import re
from typing import AsyncGenerator, Coroutine, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import morecantile
import numpy
from cogeo_mosaic.backends import MosaicBackend
from cogeo_mosaic.mosaic import MosaicJSON
from cogeo_mosaic.utils import get_footprints
from rio_tiler_crs import COGReader
from rio_tiler_crs.cogeo import geotiff_options

from titiler import utils
from titiler.dependencies import CommonTileParams, MosaicPath
from titiler.endpoints.cog import tile_response_codes
from titiler.errors import BadRequestError, TileNotFoundError
from titiler.models.cog import cogBounds
from titiler.models.mapbox import TileJSON
from titiler.models.mosaic import CreateMosaicJSON, UpdateMosaicJSON, mosaicInfo
from titiler.ressources.enums import (
    ImageMimeTypes,
    ImageType,
    MimeTypes,
    PixelSelectionMethod,
)
from titiler.ressources.responses import ImgResponse, XMLResponse

from fastapi import APIRouter, Depends, Path, Query

from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="titiler/templates")


def _read_tile(url: str, *args, **kwargs) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """Read tile from an asset"""
    with COGReader(url) as cog:
        tile, mask = cog.tile(*args, **kwargs)
    return tile, mask


def _read_point(asset: str, *args, **kwargs) -> List:
    """Read pixel value at a point from an asset"""
    with COGReader(asset) as cog:
        return cog.point(*args, **kwargs)


async def _process_futures(
    futures: List[Coroutine], concurrency: int
) -> AsyncGenerator:
    """Create an async generator which executes coroutines at specified concurrency and yields response as completed"""
    semaphore = asyncio.Semaphore(concurrency)
    async with semaphore:
        for fut in asyncio.as_completed(futures):
            yield fut


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
    mosaic_path: str = Depends(MosaicPath),
):
    """Create TileJSON"""
    kwargs = {"z": "{z}", "x": "{x}", "y": "{y}", "scale": tile_scale}
    if tile_format:
        kwargs["format"] = tile_format
    tile_url = request.url_for("mosaic_tile", **kwargs).replace("\\", "")
    with MosaicBackend(mosaic_path) as mosaic:
        tjson = TileJSON(**mosaic.metadata, tiles=[tile_url])
    return tjson


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

    with utils.Timer() as t:
        with MosaicBackend(mosaic_path) as mosaic:
            assets = mosaic.point(lon, lat)

    timings.append(("Read-mosaic", t.elapsed))

    # Rio-tiler provides a helper function (``rio_tiler.reader.multi_point``) for reading a point from multiple assets
    # using an external threadpool.  For similar reasons as described below, we will transcribe the rio-tiler code to
    # use the default executor provided by the event loop.
    futures = [
        run_in_threadpool(
            _read_point, asset, lon, lat, indexes=indexes, expression=expression
        )
        for asset in assets
    ]

    values = []
    with utils.Timer() as t:
        async for fut in _process_futures(
            futures, concurrency=int(os.getenv("MOSAIC_CONCURRENCY", 10))
        ):
            try:
                values.append(await fut)
            except Exception:
                continue

    timings.append(("Read-tiles", t.elapsed))

    if timings:
        headers["X-Server-Timings"] = "; ".join(
            ["{} - {:0.2f}".format(name, time * 1000) for (name, time) in timings]
        )

    return {"coordinates": [lon, lat], "values": values}


@router.get(r"/tiles/{z}/{x}/{y}", **tile_response_codes)
@router.get(r"/tiles/{z}/{x}/{y}.{format}", **tile_response_codes)
@router.get(r"/tiles/{z}/{x}/{y}@{scale}x", **tile_response_codes)
@router.get(r"/tiles/{z}/{x}/{y}@{scale}x.{format}", **tile_response_codes)
@router.get(r"/tiles/WebMercatorQuad/{z}/{x}/{y}.{format}", **tile_response_codes)
@router.get(r"/tiles/WebMercatorQuad/{z}/{x}/{y}@{scale}x", **tile_response_codes)
@router.get(
    r"/tiles/WebMercatorQuad/{z}/{x}/{y}@{scale}x.{format}", **tile_response_codes
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
    pixsel = pixel_selection.method()
    timings = []
    headers: Dict[str, str] = {}

    with utils.Timer() as t:
        with MosaicBackend(mosaic_path) as mosaic:
            assets = mosaic.tile(x=x, y=y, z=z)
            if not assets:
                raise TileNotFoundError(f"No assets found for tile {z}/{x}/{y}")
    timings.append(("Read-mosaic", t.elapsed))

    tilesize = 256 * scale

    # Rio-tiler-mosaic uses an external ThreadPoolExecutor to process multiple assets at once but we want to use the
    # executor provided by the event loop.  Instead of calling ``rio_tiler_mosaic.mosaic.mosaic_tiler`` directly we will
    # transcribe the code here and use the executor provided by the event loop.  This also means we define this function
    # as a coroutine (even though nothing that is called is a coroutine), since the event loop's executor isn't
    # available in normal ``def`` functions.
    futures = [
        run_in_threadpool(
            _read_tile,
            asset,
            x,
            y,
            z,
            tilesize=tilesize,
            indexes=image_params.indexes,
            expression=image_params.expression,
            nodata=image_params.nodata,
            **image_params.kwargs,
        )
        for asset in assets
    ]

    with utils.Timer() as t:
        async for fut in _process_futures(
            futures, concurrency=int(os.getenv("MOSAIC_CONCURRENCY", 10))
        ):
            try:
                tile, mask = await fut
            except Exception:
                # Gracefully handle exceptions
                continue

            tile = numpy.ma.array(tile)
            tile.mask = mask == 0
            pixsel.feed(tile)
            if pixsel.is_done:
                break
    timings.append(("Read-tiles", t.elapsed))

    tile, mask = pixsel.data
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
            tile, mask, img_format=format, colormap=image_params.color_map, **opts
        )
    timings.append(("Format", t.elapsed))

    if timings:
        headers["X-Server-Timings"] = "; ".join(
            ["{} - {:0.2f}".format(name, time * 1000) for (name, time) in timings]
        )

    return ImgResponse(
        content, media_type=ImageMimeTypes[format.value].value, headers=headers
    )


@router.get("/WMTSCapabilities.xml", response_class=XMLResponse, tags=["OGC"])
def wmts(
    request: Request,
    tile_format: ImageType = Query(
        ImageType.png, description="Output image type. Default is png."
    ),
    tile_scale: int = Query(
        1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
    ),
    mosaic_path: str = Depends(MosaicPath),
):
    """OGC WMTS endpoint."""
    endpoint = request.url_for("read_mosaicjson")

    kwargs = dict(request.query_params)
    kwargs.pop("tile_format", None)
    kwargs.pop("tile_scale", None)
    qs = urlencode(list(kwargs.items()))

    tms = morecantile.tms.get("WebMercatorQuad")
    with MosaicBackend(mosaic_path) as mosaic:
        minzoom = mosaic.mosaic_def.minzoom
        maxzoom = mosaic.mosaic_def.maxzoom
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
