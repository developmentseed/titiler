"""titiler app."""

import json
import logging
from logging import config as log_config
from typing import Annotated, Literal, Optional

import jinja2
import rasterio
from fastapi import Depends, FastAPI, HTTPException, Query, Security
from fastapi.security.api_key import APIKeyQuery
from rio_tiler.io import Reader, STACReader
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.templating import Jinja2Templates
from starlette_cramjam.middleware import CompressionMiddleware

from titiler.application import __version__ as titiler_version
from titiler.application.settings import ApiSettings
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.factory import (
    AlgorithmFactory,
    ColorMapFactory,
    MultiBaseTilerFactory,
    TilerFactory,
    TMSFactory,
)
from titiler.core.middleware import (
    CacheControlMiddleware,
    LoggerMiddleware,
    LowerCaseQueryStringMiddleware,
    TotalTimeMiddleware,
)
from titiler.core.models.OGC import Conformance, Landing
from titiler.core.resources.enums import MediaType
from titiler.core.utils import accept_media_type, create_html_response, update_openapi
from titiler.extensions import (
    cogValidateExtension,
    cogViewerExtension,
    stacExtension,
    stacRenderExtension,
    stacViewerExtension,
)
from titiler.mosaic.errors import MOSAIC_STATUS_CODES
from titiler.mosaic.factory import MosaicTilerFactory

logging.getLogger("botocore.credentials").disabled = True
logging.getLogger("botocore.utils").disabled = True
logging.getLogger("rasterio.session").setLevel(logging.ERROR)
logging.getLogger("rio-tiler").setLevel(logging.ERROR)

api_settings = ApiSettings()

# custom template directory
templates_location = (
    [jinja2.FileSystemLoader(api_settings.template_directory)]
    if api_settings.template_directory
    else []
)
# default template directory
templates_location.extend(
    [
        jinja2.PackageLoader("titiler.application", "templates"),
        jinja2.PackageLoader("titiler.core", "templates"),
    ]
)

jinja2_env = jinja2.Environment(
    autoescape=jinja2.select_autoescape(["html", "xml"]),
    loader=jinja2.ChoiceLoader(templates_location),
)
titiler_templates = Jinja2Templates(env=jinja2_env)

app_dependencies = []
if api_settings.global_access_token:
    ###############################################################################
    # Setup a global API access key, if configured
    api_key_query = APIKeyQuery(name="access_token", auto_error=False)

    def validate_access_token(access_token: str = Security(api_key_query)):
        """Validates API key access token, set as the `api_settings.global_access_token` value.
        Returns True if no access token is required, or if the access token is valid.
        Raises an HTTPException (401) if the access token is required but invalid/missing.
        """
        if not access_token:
            raise HTTPException(status_code=401, detail="Missing `access_token`")

        # if access_token == `token` then OK
        if access_token != api_settings.global_access_token:
            raise HTTPException(status_code=401, detail="Invalid `access_token`")

        return True

    app_dependencies.append(Depends(validate_access_token))


###############################################################################

app = FastAPI(
    title=api_settings.name,
    openapi_url="/api",
    docs_url="/api.html",
    description=api_settings.description,
    version=titiler_version,
    root_path=api_settings.root_path,
    dependencies=app_dependencies,
)

# Fix OpenAPI response header for OGC Common compatibility
update_openapi(app)

TITILER_CONFORMS_TO = {
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/landing-page",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/oas30",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/html",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/json",
}


###############################################################################
# Simple Dataset endpoints (e.g Cloud Optimized GeoTIFF)
if not api_settings.disable_cog:
    cog = TilerFactory(
        reader=Reader,
        router_prefix="/cog",
        add_ogc_maps=True,
        extensions=[
            cogValidateExtension(),
            cogViewerExtension(),
            stacExtension(),
        ],
        enable_telemetry=api_settings.telemetry_enabled,
        templates=titiler_templates,
    )

    app.include_router(
        cog.router,
        prefix="/cog",
        tags=["Cloud Optimized GeoTIFF"],
    )

    TITILER_CONFORMS_TO.update(cog.conforms_to)

###############################################################################
# STAC endpoints
if not api_settings.disable_stac:
    stac = MultiBaseTilerFactory(
        reader=STACReader,
        router_prefix="/stac",
        add_ogc_maps=True,
        extensions=[
            stacViewerExtension(),
            stacRenderExtension(),
        ],
        enable_telemetry=api_settings.telemetry_enabled,
        templates=titiler_templates,
    )

    app.include_router(
        stac.router,
        prefix="/stac",
        tags=["SpatioTemporal Asset Catalog"],
    )

    TITILER_CONFORMS_TO.update(stac.conforms_to)

###############################################################################
# Mosaic endpoints
if not api_settings.disable_mosaic:
    mosaic = MosaicTilerFactory(
        router_prefix="/mosaicjson",
        enable_telemetry=api_settings.telemetry_enabled,
        templates=titiler_templates,
    )
    app.include_router(
        mosaic.router,
        prefix="/mosaicjson",
        tags=["MosaicJSON"],
    )

    TITILER_CONFORMS_TO.update(mosaic.conforms_to)

###############################################################################
# TileMatrixSets endpoints
tms = TMSFactory(templates=titiler_templates)
app.include_router(
    tms.router,
    tags=["Tiling Schemes"],
)
TITILER_CONFORMS_TO.update(tms.conforms_to)

###############################################################################
# Algorithms endpoints
algorithms = AlgorithmFactory(templates=titiler_templates)
app.include_router(
    algorithms.router,
    tags=["Algorithms"],
)
TITILER_CONFORMS_TO.update(algorithms.conforms_to)

###############################################################################
# Colormaps endpoints
cmaps = ColorMapFactory(templates=titiler_templates)
app.include_router(
    cmaps.router,
    tags=["ColorMaps"],
)
TITILER_CONFORMS_TO.update(cmaps.conforms_to)


add_exception_handlers(app, DEFAULT_STATUS_CODES)
add_exception_handlers(app, MOSAIC_STATUS_CODES)

# Set all CORS enabled origins
if api_settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.cors_origins,
        allow_credentials=True,
        allow_methods=api_settings.cors_allow_methods,
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
    cachecontrol=api_settings.cachecontrol,
    exclude_path={r"/healthz"},
)

if api_settings.debug:
    app.add_middleware(LoggerMiddleware)
    app.add_middleware(TotalTimeMiddleware)

    log_config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "detailed": {
                    "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
                },
                "request": {
                    "format": (
                        "%(asctime)s - %(levelname)s - %(name)s - %(message)s "
                        + json.dumps(
                            {
                                k: f"%({k})s"
                                for k in [
                                    "http.method",
                                    "http.referer",
                                    "http.request.header.origin",
                                    "http.route",
                                    "http.target",
                                    "http.request.header.content-length",
                                    "http.request.header.accept-encoding",
                                    "http.request.header.origin",
                                    "titiler.path_params",
                                    "titiler.query_params",
                                ]
                            }
                        )
                    ),
                },
            },
            "handlers": {
                "console_detailed": {
                    "class": "logging.StreamHandler",
                    "level": "WARNING",
                    "formatter": "detailed",
                    "stream": "ext://sys.stdout",
                },
                "console_request": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "request",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "titiler": {
                    "level": "INFO",
                    "handlers": ["console_detailed"],
                    "propagate": False,
                },
                "titiler.requests": {
                    "level": "INFO",
                    "handlers": ["console_request"],
                    "propagate": False,
                },
            },
        }
    )


if api_settings.lower_case_query_parameters:
    app.add_middleware(LowerCaseQueryStringMiddleware)


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
        "title": "TiTiler",
        "description": "A modern dynamic tile server built on top of FastAPI and Rasterio/GDAL.",
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
                "title": "List of Available TileMatrixSets",
                "href": str(request.url_for("tilematrixsets")),
                "type": "application/json",
                "rel": "http://www.opengis.net/def/rel/ogc/1.0/tiling-schemes",
            },
            {
                "title": "List of Available Algorithms",
                "href": str(request.url_for("available_algorithms")),
                "type": "application/json",
                "rel": "data",
            },
            {
                "title": "List of Available ColorMaps",
                "href": str(request.url_for("available_colormaps")),
                "type": "application/json",
                "rel": "data",
            },
            {
                "title": "TiTiler Documentation (external link)",
                "href": "https://developmentseed.org/titiler/",
                "type": "text/html",
                "rel": "doc",
            },
            {
                "title": "TiTiler source code (external link)",
                "href": "https://github.com/developmentseed/titiler",
                "type": "text/html",
                "rel": "doc",
            },
        ],
    }

    if f:
        output_type = MediaType[f]
    else:
        accepted_media = [MediaType.html, MediaType.json]
        output_type = (
            accept_media_type(request.headers.get("accept", ""), accepted_media)
            or MediaType.json
        )

    if output_type == MediaType.html:
        return create_html_response(
            request,
            data,
            title="TiTiler",
            template_name="landing",
            templates=titiler_templates,
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

    if f:
        output_type = MediaType[f]
    else:
        accepted_media = [MediaType.html, MediaType.json]
        output_type = (
            accept_media_type(request.headers.get("accept", ""), accepted_media)
            or MediaType.json
        )

    if output_type == MediaType.html:
        return create_html_response(
            request,
            data,
            title="Conformance",
            template_name="conformance",
            templates=titiler_templates,
        )

    return data


if api_settings.telemetry_enabled:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    LoggingInstrumentor().instrument(set_logging_format=True)
    FastAPIInstrumentor.instrument_app(app)

    resource = Resource.create(
        {
            SERVICE_NAME: "titiler",
            SERVICE_VERSION: titiler_version,
        }
    )

    provider = TracerProvider(resource=resource)

    # uses the OTEL_EXPORTER_OTLP_ENDPOINT env var
    processor = BatchSpanProcessor(OTLPSpanExporter())
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
