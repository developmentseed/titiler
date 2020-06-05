"""API metadata."""

from typing import Dict

from rio_tiler_crs import COGReader
from stac_tiler import STACReader

from fastapi import APIRouter, Query, Depends
from starlette.requests import Request
from starlette.responses import Response

from titiler.models.metadata import cogBounds, cogInfo, cogMetadata
from titiler.api.deps import CommonMetadataParams


router = APIRouter()


@router.get(
    "/cog/bounds",
    response_model=cogBounds,
    responses={200: {"description": "Return the bounds of the COG."}},
    tags=["COG"],
)
async def cog_bounds(
    resp: Response, url: str = Query(..., description="Cloud Optimized GeoTIFF URL."),
):
    """Return the bounds of the COG."""
    resp.headers["Cache-Control"] = "max-age=3600"
    with COGReader(url) as cog:
        return {"bounds": cog.bounds}


@router.get(
    "/cog/info",
    response_model=cogInfo,
    response_model_exclude={"minzoom", "maxzoom", "center"},
    response_model_exclude_none=True,
    responses={200: {"description": "Return basic info on COG."}},
    tags=["COG"],
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
    "/cog/metadata",
    response_model=cogMetadata,
    response_model_exclude={"minzoom", "maxzoom", "center"},
    response_model_exclude_none=True,
    responses={200: {"description": "Return the metadata of the COG."}},
    tags=["COG"],
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


@router.get(
    "/stac/bounds",
    response_model=cogBounds,
    responses={200: {"description": "Return the bounds of the STAC item."}},
    tags=["STAC"],
)
async def stac_bounds(
    resp: Response, url: str = Query(..., description="STAC item URL."),
):
    """Return the bounds of the STAC item."""
    resp.headers["Cache-Control"] = "max-age=3600"
    with STACReader(url) as stac:
        return {"bounds": stac.bounds}


@router.get(
    "/stac/info",
    response_model=Dict[str, cogInfo],
    response_model_exclude={"__all__": {"minzoom", "maxzoom", "center"}},
    response_model_exclude_none=True,
    responses={200: {"description": "Return basic info for STAC item's assets"}},
    tags=["STAC"],
)
async def stac_info(
    resp: Response,
    url: str = Query(..., description="STAC item URL."),
    assets: str = Query(..., description="Comma (,) separated list of asset names."),
):
    """Return basic info on STAC item's COG."""
    resp.headers["Cache-Control"] = "max-age=3600"
    with STACReader(url) as stac:
        info = stac.info(assets.split(","))

    return info


@router.get(
    "/stac/metadata",
    response_model=Dict[str, cogMetadata],
    response_model_exclude={"__all__": {"minzoom", "maxzoom", "center"}},
    response_model_exclude_none=True,
    responses={200: {"description": "Return the metadata for STAC item's assets."}},
    tags=["STAC"],
)
async def stac_metadata(
    request: Request,
    resp: Response,
    url: str = Query(..., description="STAC item URL."),
    assets: str = Query(..., description="Comma (,) separated list of asset names."),
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
    kwargs.pop("assets", None)

    with STACReader(url) as stac:
        info = stac.metadata(
            assets.split(","),
            metadata_params.pmin,
            metadata_params.pmax,
            nodata=metadata_params.nodata,
            indexes=metadata_params.indexes,
            max_size=metadata_params.max_size,
            hist_options=metadata_params.hist_options,
            **kwargs,
        )

    resp.headers["Cache-Control"] = "max-age=3600"
    return info
