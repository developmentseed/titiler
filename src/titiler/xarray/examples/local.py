# /// script
# dependencies = [
#   "titiler.xarray[full]",
#   "starlette_cramjam",
#   "uvicorn",
# ]
# ///
"""Example of Application."""

from datetime import datetime

import numpy
import xarray
from fastapi import FastAPI
from rio_tiler.io.xarray import XarrayReader
from starlette.middleware.cors import CORSMiddleware
from starlette_cramjam.middleware import CompressionMiddleware

from titiler.core.dependencies import DefaultDependency
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.factory import AlgorithmFactory, ColorMapFactory, TMSFactory
from titiler.core.middleware import CacheControlMiddleware
from titiler.xarray.factory import TilerFactory


def XarrayDataArray() -> xarray.DataArray:
    """Custom Dependency which return a DataArray."""
    arr = numpy.linspace(1, 1000, 1000 * 2000).reshape(1, 1000, 2000)
    data = xarray.DataArray(
        arr,
        dims=("time", "y", "x"),
        coords={
            "x": numpy.arange(-170, 170, 0.17),
            "y": numpy.arange(-80, 80, 0.16),
            "time": [datetime(2022, 1, 1)],
        },
    )
    data.attrs.update({"valid_min": arr.min(), "valid_max": arr.max(), "fill_value": 0})
    data.rio.write_crs("epsg:4326", inplace=True)
    return data


app = FastAPI(
    title="TiTiler with support of Multidimensional dataset",
    openapi_url="/api",
    docs_url="/api.html",
    version="0.1.0",
)


md = TilerFactory(
    router_prefix="/md",
    # Use rio-tiler XarrayReader which accept xarray.DataArray as input
    reader=XarrayReader,
    # Use our custom dependency which return a xarray.DataArray
    path_dependency=XarrayDataArray,
    # Set the reader_dependency to `empty`
    reader_dependency=DefaultDependency,
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
