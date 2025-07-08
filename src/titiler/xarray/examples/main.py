# /// script
# dependencies = [
#   "titiler.xarray[full]",
#   "starlette_cramjam",
#   "uvicorn",
# ]
# ///
"""Example of Application."""

import os
from typing import Annotated, Literal, Optional

import rasterio
import xarray
import zarr
from fastapi import FastAPI, Query
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette_cramjam.middleware import CompressionMiddleware

from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.factory import AlgorithmFactory, ColorMapFactory, TMSFactory
from titiler.core.middleware import CacheControlMiddleware
from titiler.core.models.OGC import Conformance, Landing
from titiler.core.resources.enums import MediaType
from titiler.core.templating import create_html_response
from titiler.core.utils import accept_media_type, update_openapi
from titiler.xarray import __version__ as titiler_version
from titiler.xarray.extensions import DatasetMetadataExtension
from titiler.xarray.factory import TilerFactory

app = FastAPI(
    title="TiTiler with support of Multidimensional dataset",
    description="""A modern dynamic tile server built on top of FastAPI and Rasterio/GDAL/Xarray for Zarr/NetCDF dataset.

---

**Documentation**: <a href="https://developmentseed.org/titiler/" target="_blank">https://developmentseed.org/titiler/</a>

**Source Code**: <a href="https://github.com/developmentseed/titiler" target="_blank">https://github.com/developmentseed/titiler</a>

---
    """,
    openapi_url="/api",
    docs_url="/api.html",
    version=titiler_version,
)

update_openapi(app)

TITILER_CONFORMS_TO = {
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/req/core",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/req/landing-page",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/req/oas30",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/req/html",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/req/json",
}


md = TilerFactory(
    extensions=[
        DatasetMetadataExtension(),
    ],
)
app.include_router(md.router, tags=["Multi Dimensional"])

TITILER_CONFORMS_TO.update(md.conforms_to)

# TileMatrixSets endpoints
tms = TMSFactory()
app.include_router(tms.router, tags=["Tiling Schemes"])
TITILER_CONFORMS_TO.update(tms.conforms_to)

###############################################################################
# Algorithms endpoints
algorithms = AlgorithmFactory()
app.include_router(
    algorithms.router,
    tags=["Algorithms"],
)
TITILER_CONFORMS_TO.update(algorithms.conforms_to)

# Colormaps endpoints
cmaps = ColorMapFactory()
app.include_router(
    cmaps.router,
    tags=["ColorMaps"],
)
TITILER_CONFORMS_TO.update(cmaps.conforms_to)

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

if os.getenv("TITILER_API_TELEMETRY_ENABLED"):
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    FastAPIInstrumentor.instrument_app(app)

    resource = Resource.create(
        {
            "service.name": "titiler-xarray",
            "service.version": titiler_version,
        }
    )

    provider = TracerProvider(resource=resource)

    # uses the OTEL_EXPORTER_OTLP_ENDPOINT env var
    processor = BatchSpanProcessor(OTLPSpanExporter())
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)


@app.get(
    "/healthz",
    description="Health Check.",
    summary="Health Check.",
    operation_id="healthCheck",
    tags=["Health Check"],
)
def application_health_check():
    """Health check."""
    return {
        "versions": {
            "titiler": titiler_version,
            "rasterio": rasterio.__version__,
            "gdal": rasterio.__gdal_version__,
            "proj": rasterio.__proj_version__,
            "geos": rasterio.__geos_version__,
            "xarray": xarray.__version__,
            "zarr": zarr.__version__,
        }
    }


@app.get(
    "/",
    response_model=Landing,
    response_model_exclude_none=True,
    responses={
        200: {
            "content": {
                "text/html": {},
                "application/json": {},
            }
        },
    },
    tags=["OGC Common"],
)
def landing(
    request: Request,
    f: Annotated[
        Optional[Literal["html", "json"]],
        Query(
            description="Response MediaType. Defaults to endpoint's default or value defined in `accept` header."
        ),
    ] = None,
):
    """TiTiler landing page."""
    data = {
        "title": "TiTiler + Xarray",
        "description": "A modern dynamic tile server built on top of FastAPI and Rasterio/GDAL/Xarray for Zarr/NetCDF dataset.",
        "links": [
            {
                "title": "Landing page",
                "href": str(request.url_for("landing")),
                "type": "text/html",
                "rel": "self",
            },
            {
                "title": "The API definition (JSON)",
                "href": str(request.url_for("openapi")),
                "type": "application/vnd.oai.openapi+json;version=3.0",
                "rel": "service-desc",
            },
            {
                "title": "The API documentation",
                "href": str(request.url_for("swagger_ui_html")),
                "type": "text/html",
                "rel": "service-doc",
            },
            {
                "title": "Conformance Declaration",
                "href": str(request.url_for("conformance")),
                "type": "text/html",
                "rel": "http://www.opengis.net/def/rel/ogc/1.0/conformance",
            },
            {
                "title": "TiTiler Documentation (external link)",
                "href": "https://developmentseed.org/titiler/",
                "type": "text/html",
                "rel": "doc",
            },
            {
                "title": "TiTiler.Xarray source code (external link)",
                "href": "https://github.com/developmentseed/titiler/tree/main/src/titiler/xarray",
                "type": "text/html",
                "rel": "doc",
            },
        ],
    }

    output_type: Optional[MediaType]
    if f:
        output_type = MediaType[f]
    else:
        accepted_media = [MediaType.html, MediaType.json]
        output_type = accept_media_type(
            request.headers.get("accept", ""), accepted_media
        )

    if output_type == MediaType.html:
        return create_html_response(
            request,
            data,
            title="TiTiler",
            template_name="landing",
        )

    return data


@app.get(
    "/conformance",
    response_model=Conformance,
    response_model_exclude_none=True,
    responses={
        200: {
            "content": {
                "text/html": {},
                "application/json": {},
            }
        },
    },
    tags=["OGC Common"],
)
def conformance(
    request: Request,
    f: Annotated[
        Optional[Literal["html", "json"]],
        Query(
            description="Response MediaType. Defaults to endpoint's default or value defined in `accept` header."
        ),
    ] = None,
):
    """Conformance classes.

    Called with `GET /conformance`.

    Returns:
        Conformance classes which the server conforms to.

    """
    data = {"conformsTo": sorted(TITILER_CONFORMS_TO)}

    output_type: Optional[MediaType]
    if f:
        output_type = MediaType[f]
    else:
        accepted_media = [MediaType.html, MediaType.json]
        output_type = accept_media_type(
            request.headers.get("accept", ""), accepted_media
        )

    if output_type == MediaType.html:
        return create_html_response(
            request,
            data,
            title="Conformance",
            template_name="conformance",
        )

    return data


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app, host="127.0.0.1", port=8080, log_level="info")
