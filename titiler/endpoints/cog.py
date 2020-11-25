"""TiTiler COG Demo endpoint."""

from rio_cogeo.cogeo import cog_info as rio_cogeo_info
from rio_tiler.io import COGReader

from ..dependencies import PathParams
from ..models.cogeo import Info
from ..templates import templates
from .factory import TilerFactory

from fastapi import Depends, Query

from starlette.requests import Request
from starlette.responses import HTMLResponse

# Create Router using Tiler Factory
cog = TilerFactory(reader=COGReader, router_prefix="cog")


@cog.router.get("/validate", response_model=Info)
def cog_validate(
    src_path: PathParams = Depends(),
    strict: bool = Query(False, description="Treat warnings as errors"),
):
    """Validate a COG"""
    return rio_cogeo_info(src_path.url, strict=strict)


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
