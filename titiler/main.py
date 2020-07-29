"""titiler app."""
from titiler import settings, version
from titiler.api import api as titilerAPI
from titiler.db.memcache import CacheLayer
from titiler.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.templates.factory import web_template

from fastapi import Depends, FastAPI

from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse

if settings.MEMCACHE_HOST and not settings.DISABLE_CACHE:
    cache = CacheLayer.create_from_env()
else:
    cache = None


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/v1/openapi.json",
    description="A lightweight Cloud Optimized GeoTIFF tile server",
    version=version,
)
add_exception_handlers(app, DEFAULT_STATUS_CODES)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    origins = [origin.strip() for origin in settings.BACKEND_CORS_ORIGINS.split(",")]
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
