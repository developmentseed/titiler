"""TiTiler STAC demo endpoints."""

from rio_tiler.io import STACReader

from titiler.application.custom import ColorMapParams, TMSParams, templates
from titiler.core.factory import MultiBaseTilerFactory

from starlette.requests import Request
from starlette.responses import HTMLResponse

stac = MultiBaseTilerFactory(
    reader=STACReader,
    colormap_dependency=ColorMapParams,
    tms_dependency=TMSParams,
    router_prefix="stac",
)


@stac.router.get("/viewer", response_class=HTMLResponse)
def stac_demo(request: Request):
    """STAC Viewer."""
    return templates.TemplateResponse(
        name="stac_index.html",
        context={
            "request": request,
            "tilejson": stac.url_for(request, "tilejson"),
            "metadata": stac.url_for(request, "info"),
            "get_assets": stac.url_for(request, "available_assets"),
        },
        media_type="text/html",
    )


router = stac.router
