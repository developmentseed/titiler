"""TiTiler COG demo endpoints."""

from rio_cogeo.cogeo import cog_info as rio_cogeo_info
from rio_cogeo.models import Info
from rio_tiler.io import COGReader

from titiler.application.custom import ColorMapParams, TMSParams, templates
from titiler.core.dependencies import DatasetPathParams
from titiler.core.factory import TilerFactory

from fastapi import Depends, Query

from starlette.requests import Request
from starlette.responses import HTMLResponse

cog = TilerFactory(
    reader=COGReader,
    colormap_dependency=ColorMapParams,
    tms_dependency=TMSParams,
    router_prefix="cog",
)


@cog.router.get("/validate", response_model=Info)
def cog_validate(
    src_path: str = Depends(DatasetPathParams),
    strict: bool = Query(False, description="Treat warnings as errors"),
):
    """Validate a COG"""
    return rio_cogeo_info(src_path, strict=strict)


@cog.router.get("/viewer", response_class=HTMLResponse)
def cog_demo(request: Request):
    """COG Viewer."""
    return templates.TemplateResponse(
        name="cog_index.html",
        context={
            "request": request,
            "tilejson": cog.url_for(request, "tilejson"),
            "metadata": cog.url_for(request, "metadata"),
        },
        media_type="text/html",
    )


router = cog.router
