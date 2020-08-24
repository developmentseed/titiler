"""Titiler demo pages."""

import pkg_resources

from fastapi import APIRouter

from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

router = APIRouter()
template_dir = pkg_resources.resource_filename("titiler", "templates")
templates = Jinja2Templates(directory=template_dir)


@router.get("/cog/viewer", response_class=HTMLResponse, tags=["Demo"])
def cog_demo(request: Request):
    """COG Viewer."""
    return templates.TemplateResponse(
        name="cog_index.html", context={"request": request}, media_type="text/html",
    )


@router.get("/stac/viewer", response_class=HTMLResponse, tags=["Demo"])
def stac_demo(request: Request):
    """STAC Viewer."""
    return templates.TemplateResponse(
        name="stac_index.html", context={"request": request}, media_type="text/html",
    )
