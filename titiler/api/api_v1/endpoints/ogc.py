"""API ogc."""

from urllib.parse import urlencode

from fastapi import APIRouter, Query
from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates

from rio_tiler_crs import COGReader

from titiler.core import config
from titiler.api.deps import TileMatrixSetNames, morecantile
from titiler.ressources.enums import ImageType
from titiler.ressources.common import mimetype
from titiler.ressources.responses import XMLResponse

router = APIRouter()
templates = Jinja2Templates(directory="titiler/templates")


@router.get("/cogs/WMTSCapabilities.xml", response_class=XMLResponse)
@router.get("/cogs/{identifier}/WMTSCapabilities.xml", response_class=XMLResponse)
def wtms(
    request: Request,
    response: Response,
    identifier: TileMatrixSetNames = Query(
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
    """Wmts endpoit."""
    scheme = request.url.scheme
    host = request.headers["host"]
    if config.API_VERSION_STR:
        host += config.API_VERSION_STR
    endpoint = f"{scheme}://{host}"

    kwargs = dict(request.query_params)
    kwargs.pop("tile_format", None)
    kwargs.pop("tile_scale", None)
    qs = urlencode(list(kwargs.items()))

    tms = morecantile.tms.get(identifier.name)
    with COGReader(url, tms=tms) as cog:
        minzoom, maxzoom, bounds = cog.minzoom, cog.maxzoom, cog.bounds

    media_type = mimetype[tile_format.value]
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
