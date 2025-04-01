# /// script
# dependencies = [
#   "titiler.xarray[full]",
#   "starlette_cramjam",
#   "uvicorn",
# ]
# ///
"""Example of Application."""

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette_cramjam.middleware import CompressionMiddleware

from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.factory import AlgorithmFactory, ColorMapFactory, TMSFactory
from titiler.core.middleware import CacheControlMiddleware
from titiler.xarray.extensions import DatasetMetadataExtension
from titiler.xarray.factory import TilerFactory

app = FastAPI(
    title="TiTiler with support of Multidimensional dataset",
    openapi_url="/api",
    docs_url="/api.html",
    version="0.1.0",
)


md = TilerFactory(
    router_prefix="/md",
    extensions=[
        DatasetMetadataExtension(),
    ],
)
app.include_router(md.router, prefix="/md", tags=["Multi Dimensional"])

# TileMatrixSets endpoints
app.include_router(TMSFactory().router, tags=["Tiling Schemes"])

###############################################################################
# Algorithms endpoints
app.include_router(
    AlgorithmFactory().router,
    tags=["Algorithms"],
)

# Colormaps endpoints
app.include_router(
    ColorMapFactory().router,
    tags=["ColorMaps"],
)

add_exception_handlers(app, DEFAULT_STATUS_CODES)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.add_middleware(
    CompressionMiddleware,
    minimum_size=0,
    exclude_mediatype={
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/jp2",
        "image/webp",
    },
    compression_level=6,
)

app.add_middleware(
    CacheControlMiddleware,
    cachecontrol="public, max-age=3600",
    exclude_path={r"/healthz"},
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app, host="127.0.0.1", port=8080, log_level="info")
