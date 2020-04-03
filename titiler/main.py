"""titiler app."""
from typing import Any, Dict

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware


from titiler import version
from titiler.core import config
from titiler.db.memcache import CacheLayer
from titiler.api.api_v1.api import api_router

templates = Jinja2Templates(directory="titiler/templates")

if config.MEMCACHE_HOST and not config.DISABLE_CACHE:
    kwargs: Dict[str, Any] = {
        k: v
        for k, v in zip(
            ["port", "user", "password"],
            [config.MEMCACHE_PORT, config.MEMCACHE_USERNAME, config.MEMCACHE_PASSWORD],
        )
        if v
    }
    cache = CacheLayer(config.MEMCACHE_HOST, **kwargs)
else:
    cache = None


app = FastAPI(
    title=config.PROJECT_NAME,
    openapi_url="/api/v1/openapi.json",
    description="A lightweight Cloud Optimized GeoTIFF tile server",
    version=version,
)

# Set all CORS enabled origins
if config.BACKEND_CORS_ORIGINS:
    origins = [origin.strip() for origin in config.BACKEND_CORS_ORIGINS.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

app.add_middleware(GZipMiddleware, minimum_size=0)


@app.middleware("http")
async def cache_middleware(request: Request, call_next):
    """Add cache layer."""
    request.state.cache = cache
    response = await call_next(request)
    if cache:
        request.state.cache.client.disconnect_all()
    return response


@app.get(
    "/",
    responses={200: {"content": {"application/hmtl": {}}}},
    response_class=HTMLResponse,
)
@app.get(
    "/index.html",
    responses={200: {"content": {"application/hmtl": {}}}},
    response_class=HTMLResponse,
)
def index(request: Request):
    """Demo Page."""
    scheme = request.url.scheme
    host = request.headers["host"]
    if config.API_VERSION_STR:
        host += config.API_VERSION_STR
    endpoint = f"{scheme}://{host}"

    return templates.TemplateResponse(
        "index.html", {"request": request, "endpoint": endpoint}, media_type="text/html"
    )


@app.get(
    "/simple_viewer.html",
    responses={200: {"content": {"application/hmtl": {}}}},
    response_class=HTMLResponse,
)
def simple(request: Request):
    """Demo Page."""
    scheme = request.url.scheme
    host = request.headers["host"]
    if config.API_VERSION_STR:
        host += config.API_VERSION_STR
    endpoint = f"{scheme}://{host}"

    return templates.TemplateResponse(
        "simple.html",
        {"request": request, "endpoint": endpoint},
        media_type="text/html",
    )


@app.get("/ping", description="Health Check")
def ping():
    """Health check."""
    return {"ping": "pong!"}


app.include_router(api_router, prefix=config.API_VERSION_STR)
