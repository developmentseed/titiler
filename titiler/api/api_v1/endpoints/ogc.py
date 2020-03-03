"""API ogc."""

import urllib

from fastapi import APIRouter, Query
from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates

import rasterio
from rasterio import warp
from rio_tiler.mercator import get_zooms

from titiler.core import config
from titiler.ressources.enums import ImageType
from titiler.ressources.common import mimetype
from titiler.ressources.responses import XMLResponse

router = APIRouter()
templates = Jinja2Templates(directory="titiler/templates")


@router.get(
    r"/WMTSCapabilities.xml",
    responses={200: {"content": {"application/xml": {}}}},
    response_class=XMLResponse,
)
def wtms(
    request: Request,
    response: Response,
    url: str = Query(..., title="Url of the COG"),
    tile_format: ImageType = "png",
    tile_scale: int = Query(1, gt=0, lt=4),
):
    """Wmts endpoit."""
    scheme = request.url.scheme
    host = request.headers["host"]
    if config.API_VERSION_STR:
        host += config.API_VERSION_STR
    endpoint = f"{scheme}://{host}"

    kwargs = dict(request.query_params)
    kwargs.pop("tile_format", None)
    kwargs.pop("tile_scale", None)
    qs = urllib.parse.urlencode(list(kwargs.items()))

    with rasterio.open(url) as src_dst:
        bounds = list(
            warp.transform_bounds(
                src_dst.crs, "epsg:4326", *src_dst.bounds, densify_pts=21
            )
        )
        minzoom, maxzoom = get_zooms(src_dst)

    media_type = mimetype[tile_format]
    tilesize = tile_scale * 256
    tileMatrix = []
    for zoom in range(minzoom, maxzoom + 1):
        tileMatrix.append(
            f"""<TileMatrix>
                <ows:Identifier>{zoom}</ows:Identifier>
                <ScaleDenominator>{559082264.02872 / 2 ** zoom / tile_scale}</ScaleDenominator>
                <TopLeftCorner>-20037508.34278925 20037508.34278925</TopLeftCorner>
                <TileWidth>{tilesize}</TileWidth>
                <TileHeight>{tilesize}</TileHeight>
                <MatrixWidth>{2 ** zoom}</MatrixWidth>
                <MatrixHeight>{2 ** zoom}</MatrixHeight>
            </TileMatrix>"""
        )

    return templates.TemplateResponse(
        "wmts.xml",
        {
            "request": request,
            "endpoint": endpoint,
            "bounds": bounds,
            "tileMatrix": tileMatrix,
            "title": "Cloud Optimized GeoTIFF",
            "query_string": qs,
            "tile_scale": tile_scale,
            "tile_format": tile_format.value,
            "media_type": media_type,
        },
        media_type="application/xml",
    )
