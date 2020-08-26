"""TiTiler STAC Demo endpoint."""

import pkg_resources
from rio_tiler_crs import STACReader

from .factory import TilerFactory

from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

template_dir = pkg_resources.resource_filename("titiler", "templates")
templates = Jinja2Templates(directory=template_dir)

# Create Router using Tiler Factory
stac = TilerFactory(reader=STACReader, add_asset_deps=True, router_prefix="stac")


@stac.router.get("/viewer", response_class=HTMLResponse)
def stac_demo(request: Request):
    """STAC Viewer."""
    return templates.TemplateResponse(
        name="stac_index.html",
        context={
            "request": request,
            "tilejson": request.url_for(f"{stac.router_prefix}tilejson"),
            "metadata": request.url_for(f"{stac.router_prefix}info"),
        },
        media_type="text/html",
    )


router = stac.router
