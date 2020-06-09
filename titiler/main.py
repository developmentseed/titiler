"""titiler app."""
from typing import Any, Dict

from fastapi import FastAPI, Depends
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from titiler import version
from titiler.core import config
from titiler.db.memcache import CacheLayer
from titiler.api import api as titilerAPI
from titiler.templates.factory import web_template


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


@app.get("/", response_class=HTMLResponse, tags=["Webpage"], deprecated=True)
@app.get("/index.html", response_class=HTMLResponse, tags=["Webpage"], deprecated=True)
def index(request: Request, template=Depends(web_template)):
    """Demo Page."""
    return template(request, "cog_index.html", "cog_tilejson", "cog_metadata")


@app.get("/simple.html", response_class=HTMLResponse, tags=["Webpage"], deprecated=True)
def simple(request: Request, template=Depends(web_template)):
    """Demo Page."""
    return template(request, "cog_simple.html", "cog_tilejson", "cog_info")


@app.get("/ping", description="Health Check", tags=["Health Check"])
def ping():
    """Health check."""
    return {"ping": "pong!"}


app.include_router(titilerAPI.api_router)
