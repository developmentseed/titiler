"""API landing."""

from fastapi import APIRouter

from starlette.requests import Request
from starlette.templating import Jinja2Templates
from starlette.responses import HTMLResponse

from titiler.core import config

router = APIRouter()
templates = Jinja2Templates(directory="titiler/templates")


@router.get(
    "/",
    responses={200: {"content": {"application/hmtl": {}}}},
    response_class=HTMLResponse,
)
@router.get(
    "/index.html",
    responses={200: {"content": {"application/hmtl": {}}}},
    response_class=HTMLResponse,
)
def landing(request: Request):
    """Wmts endpoit."""
    scheme = request.url.scheme
    host = request.headers["host"]
    if config.API_V1_STR:
        host += config.API_V1_STR
    endpoint = f"{scheme}://{host}"

    return templates.TemplateResponse(
        "index.html", {"request": request, "endpoint": endpoint}, media_type="text/html"
    )
