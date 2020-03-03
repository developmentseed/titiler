"""titiler app."""

from fastapi import FastAPI
from starlette.requests import Request
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware


from titiler import version
from titiler.core import config
from titiler.api.api_v1.api import api_router

from titiler.db.memcache import CacheLayer


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

app.include_router(api_router, prefix=config.API_V1_STR)

if config.MEMCACHE_HOST and not config.DISABLE_CACHE:
    kwargs = {
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


@app.middleware("http")
async def cache_middleware(request: Request, call_next):
    """Add cache layer."""
    request.state.cache = cache
    response = await call_next(request)
    if cache:
        request.state.cache.client.disconnect_all()
    return response
