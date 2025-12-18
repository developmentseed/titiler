"""TiTiler Router factories."""

import abc
import base64
import logging
import os
import warnings
from collections.abc import Callable, Sequence
from typing import Annotated, Any, Literal
from urllib.parse import urlencode

import jinja2
import numpy
import rasterio
from attrs import define, field
from fastapi import APIRouter, Body, Depends, Path, Query
from fastapi.dependencies.utils import get_parameterless_sub_dependant
from fastapi.params import Depends as DependsFunc
from geojson_pydantic.features import Feature, FeatureCollection
from morecantile import TileMatrixSet
from morecantile import tms as morecantile_tms
from morecantile.defaults import TileMatrixSets
from pydantic import Field
from rio_tiler.colormap import ColorMaps
from rio_tiler.colormap import cmap as default_cmap
from rio_tiler.constants import WGS84_CRS
from rio_tiler.io import BaseReader, MultiBandReader, MultiBaseReader, Reader
from rio_tiler.models import ImageData, Info
from rio_tiler.types import ColorMapType
from rio_tiler.utils import CRS_to_uri
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from starlette.routing import Match, NoMatchFound
from starlette.routing import Route as APIRoute
from starlette.routing import compile_path, replace_params
from starlette.templating import Jinja2Templates

from titiler.core.algorithm import (
    AlgorithmMetadata,
    Algorithms,
    AlgorithmtList,
    BaseAlgorithm,
)
from titiler.core.algorithm import algorithms as available_algorithms
from titiler.core.dependencies import (
    AssetsBidxExprParams,
    AssetsBidxExprParamsOptional,
    AssetsBidxParams,
    AssetsParams,
    BandsExprParams,
    BandsExprParamsOptional,
    BandsParams,
    BidxExprParams,
    ColorMapParams,
    CoordCRSParams,
    CRSParams,
    DatasetParams,
    DatasetPathParams,
    DefaultDependency,
    DstCRSParams,
    HistogramParams,
    ImageRenderingParams,
    OGCMapsParams,
    PartFeatureParams,
    PreviewParams,
    StatisticsParams,
    TileParams,
)
from titiler.core.models.mapbox import TileJSON
from titiler.core.models.OGC import TileMatrixSetList, TileSet, TileSetList
from titiler.core.models.responses import (
    ColorMapList,
    InfoGeoJSON,
    MultiBaseInfo,
    MultiBaseInfoGeoJSON,
    MultiBaseStatistics,
    MultiBaseStatisticsGeoJSON,
    Point,
    Statistics,
    StatisticsGeoJSON,
)
from titiler.core.resources.enums import ImageType, MediaType
from titiler.core.resources.responses import GeoJSONResponse, JSONResponse
from titiler.core.routing import EndpointScope
from titiler.core.telemetry import factory_trace
from titiler.core.utils import (
    accept_media_type,
    bounds_to_geometry,
    create_html_response,
    render_image,
    tms_limits,
)

jinja2_env = jinja2.Environment(
    autoescape=jinja2.select_autoescape(["html"]),
    loader=jinja2.ChoiceLoader([jinja2.PackageLoader(__package__, "templates")]),
)
DEFAULT_TEMPLATES = Jinja2Templates(env=jinja2_env)

img_endpoint_params: dict[str, Any] = {
    "responses": {
        200: {
            "content": {
                "image/png": {},
                "image/jpeg": {},
                "image/jpg": {},
                "image/webp": {},
                "image/jp2": {},
                "image/tiff; application=geotiff": {},
                "application/x-binary": {},
            },
            "description": "Return an image.",
        }
    },
    "response_class": Response,
}

logger = logging.getLogger(__name__)


@define
class FactoryExtension(metaclass=abc.ABCMeta):
    """Factory Extension."""

    @abc.abstractmethod
    def register(self, factory: "BaseFactory"):
        """Register extension to the factory."""
        ...


@define(kw_only=True)
class BaseFactory(metaclass=abc.ABCMeta):
    """Base Factory.

    Abstract Base Class which defines most inputs used by dynamic tiler.

    Attributes:
        router (fastapi.APIRouter): Application router to register endpoints to.
        router_prefix (str): prefix where the router will be mounted in the application.
        route_dependencies (list): Additional routes dependencies to add after routes creations.

    """

    # FastAPI router
    router: APIRouter = field(factory=APIRouter)

    # Router Prefix is needed to find the path for /tile if the TilerFactory.router is mounted
    # with other router (multiple `.../tile` routes).
    # e.g if you mount the route with `/cog` prefix, set router_prefix to cog and
    router_prefix: str = ""

    # add dependencies to specific routes
    route_dependencies: list[tuple[list[EndpointScope], list[DependsFunc]]] = field(
        factory=list
    )

    extensions: list[FactoryExtension] = field(factory=list)

    name: str | None = field(default=None)
    operation_prefix: str = field(init=False, default="")

    conforms_to: set[str] = field(factory=set)

    enable_telemetry: bool = field(default=False)

    templates: Jinja2Templates = DEFAULT_TEMPLATES

    def __attrs_post_init__(self):
        """Post Init: register route and configure specific options."""
        # prefix for endpoint's operationId
        name = self.name or self.router_prefix.replace("/", ".")
        self.operation_prefix = f"{name}." if name else ""

        # Register endpoints
        self.register_routes()

        # Register Extensions
        for ext in self.extensions:
            ext.register(self)

        # Update endpoints dependencies
        for scopes, dependencies in self.route_dependencies:
            self.add_route_dependencies(scopes=scopes, dependencies=dependencies)

        if self.enable_telemetry:
            self.add_telemetry()

    @abc.abstractmethod
    def register_routes(self):
        """Register Routes."""
        ...

    def url_for(self, request: Request, name: str, **path_params: Any) -> str:
        """Return full url (with prefix) for a specific endpoint."""
        url_path = self.router.url_path_for(name, **path_params)
        base_url = str(request.base_url)
        if self.router_prefix:
            prefix = self.router_prefix.lstrip("/")
            # If we have prefix with custom path param we check and replace them with
            # the path params provided
            if "{" in prefix:
                _, path_format, param_convertors = compile_path(prefix)
                prefix, _ = replace_params(
                    path_format, param_convertors, request.path_params.copy()
                )
            base_url += prefix

        return str(url_path.make_absolute_url(base_url=base_url))

    def add_route_dependencies(
        self,
        *,
        scopes: list[EndpointScope],
        dependencies=list[DependsFunc],
    ):
        """Add dependencies to routes.

        Allows a developer to add dependencies to a route after the route has been defined.

        """
        for route in self.router.routes:
            for scope in scopes:
                match, _ = route.matches({"type": "http", **scope})
                if match != Match.FULL:
                    continue

                # Mimicking how APIRoute handles dependencies:
                # https://github.com/tiangolo/fastapi/blob/1760da0efa55585c19835d81afa8ca386036c325/fastapi/routing.py#L408-L412
                for depends in dependencies[::-1]:
                    route.dependant.dependencies.insert(  # type: ignore
                        0,
                        get_parameterless_sub_dependant(
                            depends=depends,
                            path=route.path_format,  # type: ignore
                        ),
                    )

                # Register dependencies directly on route so that they aren't ignored if
                # the routes are later associated with an app (e.g. app.include_router(router))
                # https://github.com/tiangolo/fastapi/blob/58ab733f19846b4875c5b79bfb1f4d1cb7f4823f/fastapi/applications.py#L337-L360
                # https://github.com/tiangolo/fastapi/blob/58ab733f19846b4875c5b79bfb1f4d1cb7f4823f/fastapi/routing.py#L677-L678
                route.dependencies.extend(dependencies)  # type: ignore

    def add_telemetry(self):
        """
        Applies the factory_trace decorator to all registered API routes.

        This method iterates through the router's routes and wraps the endpoint
        of each APIRoute to ensure consistent OpenTelemetry tracing.
        """
        if not factory_trace.decorator_enabled:
            warnings.warn(
                "telemetry enabled for the factory class but tracing is not available",
                RuntimeWarning,
                stacklevel=2,
            )
            return

        for route in self.router.routes:
            if isinstance(route, APIRoute):
                route.endpoint = factory_trace(route.endpoint, factory_instance=self)


@define(kw_only=True)
class TilerFactory(BaseFactory):
    """Tiler Factory.

    Attributes:
        reader (rio_tiler.io.base.BaseReader): A rio-tiler reader. Defaults to `rio_tiler.io.Reader`.
        reader_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining BaseReader options.
        path_dependency (Callable): Endpoint dependency defining `path` to pass to the reader init.
        layer_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining dataset indexes/bands/assets options.
        dataset_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining dataset overwriting options (e.g nodata).
        tile_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining tile options (e.g buffer, padding).
        stats_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining options for rio-tiler's statistics method.
        histogram_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining options for numpy's histogram method.
        img_preview_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining options for rio-tiler's preview method.
        img_part_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining options for rio-tiler's part/feature methods.
        process_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining image post-processing options (e.g rescaling, color-formula).
        rescale_dependency (Callable[..., Optional[RescaleType]]):
        color_formula_dependency (Callable[..., Optional[str]]):
        colormap_dependency (Callable): Endpoint dependency defining ColorMap options (e.g colormap_name).
        render_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining image rendering options (e.g add_mask).
        environment_dependency (Callable): Endpoint dependency to define GDAL environment at runtime.
        supported_tms (morecantile.defaults.TileMatrixSets): TileMatrixSets object holding the supported TileMatrixSets.
        templates (Jinja2Templates): Jinja2 templates.
        add_preview (bool): add `/preview` endpoints. Defaults to True.
        add_part (bool): add `/bbox` and `/feature` endpoints. Defaults to True.
        add_viewer (bool): add `/map.html` endpoints. Defaults to True.

    """

    # Default reader is set to rio_tiler.io.Reader
    reader: type[BaseReader] = Reader

    # Reader dependency
    reader_dependency: type[DefaultDependency] = DefaultDependency

    # Path Dependency
    path_dependency: Callable[..., Any] = DatasetPathParams

    # Indexes/Expression Dependencies
    layer_dependency: type[DefaultDependency] = BidxExprParams

    # Rasterio Dataset Options (nodata, unscale, resampling, reproject)
    dataset_dependency: type[DefaultDependency] = DatasetParams

    # Tile/Tilejson/WMTS Dependencies
    tile_dependency: type[DefaultDependency] = TileParams

    # Statistics/Histogram Dependencies
    stats_dependency: type[DefaultDependency] = StatisticsParams
    histogram_dependency: type[DefaultDependency] = HistogramParams

    # Crop/Preview endpoints Dependencies
    img_preview_dependency: type[DefaultDependency] = PreviewParams
    img_part_dependency: type[DefaultDependency] = PartFeatureParams

    # Post Processing Dependencies (algorithm)
    process_dependency: Callable[..., BaseAlgorithm | None] = (
        available_algorithms.dependency
    )

    # Image rendering Dependencies
    colormap_dependency: Callable[..., ColorMapType | None] = ColorMapParams
    render_dependency: type[DefaultDependency] = ImageRenderingParams

    # GDAL ENV dependency
    environment_dependency: Callable[..., dict] = field(default=lambda: {})

    # TileMatrixSet dependency
    supported_tms: TileMatrixSets = morecantile_tms

    render_func: Callable[..., tuple[bytes, str]] = render_image

    # Add/Remove some endpoints
    add_preview: bool = True
    add_part: bool = True
    add_viewer: bool = True
    add_ogc_maps: bool = False

    conforms_to: set[str] = field(
        factory=lambda: {
            # https://docs.ogc.org/is/20-057/20-057.html#toc30
            "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/tileset",
            # https://docs.ogc.org/is/20-057/20-057.html#toc34
            "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/tilesets-list",
            # https://docs.ogc.org/is/20-057/20-057.html#toc65
            "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/core",
            "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/png",
            "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/jpeg",
            "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/tiff",
        }
    )

    def register_routes(self):
        """
        This Method register routes to the router.

        Because we wrap the endpoints in a class we cannot define the routes as
        methods (because of the self argument). The HACK is to define routes inside
        the class method and register them after the class initialization.

        """
        # Default Routes
        # (/info, /statistics, /tiles, /tilejson.json, and /point)
        self.info()
        self.statistics()
        self.tilesets()
        self.tile()
        if self.add_viewer:
            self.map_viewer()
        self.tilejson()
        self.point()

        # Optional Routes
        if self.add_preview:
            self.preview()

        if self.add_part:
            self.part()

        if self.add_ogc_maps:
            self.ogc_maps()

    ############################################################################
    # /info
    ############################################################################
    def info(self):
        """Register /info endpoint."""

        @self.router.get(
            "/info",
            response_model=Info,
            response_model_exclude_none=True,
            response_class=JSONResponse,
            responses={200: {"description": "Return dataset's basic info."}},
            operation_id=f"{self.operation_prefix}getInfo",
        )
        def info(
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return dataset's basic info."""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    return src_dst.info()

        @self.router.get(
            "/info.geojson",
            response_model=InfoGeoJSON,
            response_model_exclude_none=True,
            response_class=GeoJSONResponse,
            responses={
                200: {
                    "content": {"application/geo+json": {}},
                    "description": "Return dataset's basic info as a GeoJSON feature.",
                }
            },
            operation_id=f"{self.operation_prefix}getInfoGeoJSON",
        )
        def info_geojson(
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            crs=Depends(CRSParams),
            env=Depends(self.environment_dependency),
        ):
            """Return dataset's basic info as a GeoJSON feature."""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    bounds = src_dst.get_geographic_bounds(crs or WGS84_CRS)
                    geometry = bounds_to_geometry(bounds)

                    return Feature(
                        type="Feature",
                        bbox=bounds,
                        geometry=geometry,
                        properties=src_dst.info(),
                    )

    ############################################################################
    # /statistics
    ############################################################################
    def statistics(self):
        """add statistics endpoints."""

        # GET endpoint
        @self.router.get(
            "/statistics",
            response_class=JSONResponse,
            response_model=Statistics,
            responses={
                200: {
                    "content": {"application/json": {}},
                    "description": "Return dataset's statistics.",
                }
            },
            operation_id=f"{self.operation_prefix}getStatistics",
        )
        def statistics(
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_preview_dependency),
            post_process=Depends(self.process_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Dataset statistics."""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    image = src_dst.preview(
                        **layer_params.as_dict(),
                        **image_params.as_dict(),
                        **dataset_params.as_dict(),
                    )

                    if post_process:
                        image = post_process(image)

                    return image.statistics(
                        **stats_params.as_dict(),
                        hist_options=histogram_params.as_dict(),
                    )

        # POST endpoint
        @self.router.post(
            "/statistics",
            response_model=StatisticsGeoJSON,
            response_model_exclude_none=True,
            response_class=GeoJSONResponse,
            responses={
                200: {
                    "content": {"application/geo+json": {}},
                    "description": "Return dataset's statistics from feature or featureCollection.",
                }
            },
            operation_id=f"{self.operation_prefix}postStatisticsForGeoJSON",
        )
        def geojson_statistics(
            geojson: Annotated[
                FeatureCollection | Feature,
                Body(description="GeoJSON Feature or FeatureCollection."),
            ],
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            coord_crs=Depends(CoordCRSParams),
            dst_crs=Depends(DstCRSParams),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_part_dependency),
            post_process=Depends(self.process_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Statistics from a geojson feature or featureCollection."""
            fc = geojson
            if isinstance(fc, Feature):
                fc = FeatureCollection(type="FeatureCollection", features=[geojson])

            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    for feature in fc.features:
                        shape = feature.model_dump(exclude_none=True)
                        image = src_dst.feature(
                            shape,
                            shape_crs=coord_crs or WGS84_CRS,
                            dst_crs=dst_crs,
                            align_bounds_with_dataset=True,
                            **layer_params.as_dict(),
                            **image_params.as_dict(),
                            **dataset_params.as_dict(),
                        )

                        # Get the coverage % array
                        coverage_array = image.get_coverage_array(
                            shape,
                            shape_crs=coord_crs or WGS84_CRS,
                        )

                        if post_process:
                            image = post_process(image)

                        stats = image.statistics(
                            **stats_params.as_dict(),
                            hist_options=histogram_params.as_dict(),
                            coverage=coverage_array,
                        )

                        feature.properties = feature.properties or {}
                        feature.properties.update({"statistics": stats})

            return fc.features[0] if isinstance(geojson, Feature) else fc

    ############################################################################
    # /tileset
    ############################################################################
    def tilesets(self):  # noqa: C901
        """Register OGC tilesets endpoints."""

        @self.router.get(
            "/tiles",
            response_model=TileSetList,
            response_class=JSONResponse,
            response_model_exclude_none=True,
            responses={
                200: {
                    "content": {
                        "application/json": {},
                        "text/html": {},
                    }
                }
            },
            summary="Retrieve a list of available raster tilesets for the specified dataset.",
            operation_id=f"{self.operation_prefix}getTileSetList",
        )
        async def tileset_list(
            request: Request,
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            crs=Depends(CRSParams),
            env=Depends(self.environment_dependency),
            f: Annotated[
                Literal["html", "json"] | None,
                Query(
                    description="Response MediaType. Defaults to endpoint's default or value defined in `accept` header."
                ),
            ] = None,
        ):
            """Retrieve a list of available raster tilesets for the specified dataset."""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    bounds = src_dst.get_geographic_bounds(crs or WGS84_CRS)

            collection_bbox = {
                "lowerLeft": [bounds[0], bounds[1]],
                "upperRight": [bounds[2], bounds[3]],
                "crs": CRS_to_uri(crs or WGS84_CRS),
            }

            qs = [
                (key, value)
                for (key, value) in request.query_params._list
                if key.lower() not in ["crs"]
            ]
            query_string = f"?{urlencode(qs)}" if qs else ""

            attribution = os.environ.get("TITILER_DEFAULT_ATTRIBUTION")

            tilesets: list[dict[str, Any]] = []
            for tms in self.supported_tms.list():
                tileset: dict[str, Any] = {
                    "title": f"tileset tiled using {tms} TileMatrixSet",
                    "attribution": attribution,
                    "dataType": "map",
                    "crs": self.supported_tms.get(tms).crs,
                    "boundingBox": collection_bbox,
                    "links": [
                        {
                            "href": self.url_for(
                                request, "tileset", tileMatrixSetId=tms
                            )
                            + query_string,
                            "rel": "self",
                            "type": "application/json",
                            "title": f"Tileset tiled using {tms} TileMatrixSet",
                        },
                        {
                            "href": self.url_for(
                                request,
                                "tile",
                                tileMatrixSetId=tms,
                                z="{z}",
                                x="{x}",
                                y="{y}",
                            )
                            + query_string,
                            "rel": "tile",
                            "title": "Templated link for retrieving Raster tiles",
                        },
                    ],
                }

                try:
                    tileset["links"].append(
                        {
                            "href": str(
                                request.url_for("tilematrixset", tileMatrixSetId=tms)
                            ),
                            "rel": "http://www.opengis.net/def/rel/ogc/1.0/tiling-scheme",
                            "type": "application/json",
                            "title": f"Definition of '{tms}' tileMatrixSet",
                        }
                    )
                except NoMatchFound:
                    pass

                tilesets.append(tileset)

            data = TileSetList.model_validate({"tilesets": tilesets})

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
                    data.model_dump(exclude_none=True, mode="json"),
                    title="Tilesets",
                    template_name="tilesets",
                    templates=self.templates,
                )

            return data

        @self.router.get(
            "/tiles/{tileMatrixSetId}",
            response_model=TileSet,
            response_class=JSONResponse,
            response_model_exclude_none=True,
            responses={
                200: {
                    "content": {
                        "application/json": {},
                        "text/html": {},
                    }
                }
            },
            summary="Retrieve the raster tileset metadata for the specified dataset and tiling scheme (tile matrix set).",
            operation_id=f"{self.operation_prefix}getTileSet",
        )
        async def tileset(
            request: Request,
            tileMatrixSetId: Annotated[
                Literal[tuple(self.supported_tms.list())],
                Path(
                    description="Identifier selecting one of the TileMatrixSetId supported."
                ),
            ],
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
            f: Annotated[
                Literal["html", "json"] | None,
                Query(
                    description="Response MediaType. Defaults to endpoint's default or value defined in `accept` header."
                ),
            ] = None,
        ):
            """Retrieve the raster tileset metadata for the specified dataset and tiling scheme (tile matrix set)."""
            tms = self.supported_tms.get(tileMatrixSetId)
            with rasterio.Env(**env):
                with self.reader(
                    src_path, tms=tms, **reader_params.as_dict()
                ) as src_dst:
                    bounds = src_dst.get_geographic_bounds(tms.rasterio_geographic_crs)
                    minzoom = src_dst.minzoom
                    maxzoom = src_dst.maxzoom

                    collection_bbox = {
                        "lowerLeft": [bounds[0], bounds[1]],
                        "upperRight": [bounds[2], bounds[3]],
                        "crs": CRS_to_uri(tms.rasterio_geographic_crs),
                    }

                    tilematrix_limits = tms_limits(
                        tms,
                        bounds,
                        zooms=(minzoom, maxzoom),
                    )

            query_string = (
                f"?{urlencode(request.query_params._list)}"
                if request.query_params._list
                else ""
            )

            links = [
                {
                    "href": self.url_for(
                        request,
                        "tileset",
                        tileMatrixSetId=tileMatrixSetId,
                    ),
                    "rel": "self",
                    "type": "application/json",
                    "title": f"Tileset tiled using {tileMatrixSetId} TileMatrixSet",
                },
                {
                    "href": self.url_for(
                        request,
                        "tile",
                        tileMatrixSetId=tileMatrixSetId,
                        z="{z}",
                        x="{x}",
                        y="{y}",
                    )
                    + query_string,
                    "rel": "tile",
                    "title": "Templated link for retrieving Raster tiles",
                    "templated": True,
                },
            ]
            try:
                links.append(
                    {
                        "href": str(
                            request.url_for(
                                "tilematrixset", tileMatrixSetId=tileMatrixSetId
                            )
                        ),
                        "rel": "http://www.opengis.net/def/rel/ogc/1.0/tiling-scheme",
                        "type": "application/json",
                        "title": f"Definition of '{tileMatrixSetId}' tileMatrixSet",
                    }
                )
            except NoMatchFound:
                pass

            if self.add_viewer:
                links.append(
                    {
                        "href": self.url_for(
                            request,
                            "map_viewer",
                            tileMatrixSetId=tileMatrixSetId,
                        )
                        + query_string,
                        "type": "text/html",
                        "rel": "data",
                        "title": f"Map viewer for '{tileMatrixSetId}' tileMatrixSet",
                    }
                )

            data = TileSet.model_validate(
                {
                    "title": f"tileset tiled using {tileMatrixSetId} TileMatrixSet",
                    "dataType": "map",
                    "crs": tms.crs,
                    "boundingBox": collection_bbox,
                    "links": links,
                    "tileMatrixSetLimits": tilematrix_limits,
                    "attribution": os.environ.get("TITILER_DEFAULT_ATTRIBUTION"),
                }
            )

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
                    title=tileMatrixSetId,
                    template_name="tileset",
                    templates=self.templates,
                )

            return data

    ############################################################################
    # /tiles
    ############################################################################
    def tile(self):  # noqa: C901
        """Register /tiles endpoint."""

        @self.router.get(
            "/tiles/{tileMatrixSetId}/{z}/{x}/{y}",
            operation_id=f"{self.operation_prefix}getTile",
            **img_endpoint_params,
        )
        @self.router.get(
            "/tiles/{tileMatrixSetId}/{z}/{x}/{y}.{format}",
            operation_id=f"{self.operation_prefix}getTileWithFormat",
            **img_endpoint_params,
        )
        @self.router.get(
            "/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x",
            operation_id=f"{self.operation_prefix}getTileWithScale",
            **img_endpoint_params,
        )
        @self.router.get(
            "/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
            operation_id=f"{self.operation_prefix}getTileWithFormatAndScale",
            **img_endpoint_params,
        )
        def tile(
            z: Annotated[
                int,
                Path(
                    description="Identifier (Z) selecting one of the scales defined in the TileMatrixSet and representing the scaleDenominator the tile.",
                ),
            ],
            x: Annotated[
                int,
                Path(
                    description="Column (X) index of the tile on the selected TileMatrix. It cannot exceed the MatrixHeight-1 for the selected TileMatrix.",
                ),
            ],
            y: Annotated[
                int,
                Path(
                    description="Row (Y) index of the tile on the selected TileMatrix. It cannot exceed the MatrixWidth-1 for the selected TileMatrix.",
                ),
            ],
            tileMatrixSetId: Annotated[
                Literal[tuple(self.supported_tms.list())],
                Path(
                    description="Identifier selecting one of the TileMatrixSetId supported."
                ),
            ],
            scale: Annotated[
                int,
                Field(
                    gt=0, le=4, description="Tile size scale. 1=256x256, 2=512x512..."
                ),
            ] = 1,
            format: Annotated[
                ImageType | None,
                Field(
                    description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg)."
                ),
            ] = None,
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            tile_params=Depends(self.tile_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            post_process=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create map tile from a dataset."""
            tms = self.supported_tms.get(tileMatrixSetId)
            with rasterio.Env(**env):
                logger.info(f"opening data with reader: {self.reader}")
                with self.reader(
                    src_path, tms=tms, **reader_params.as_dict()
                ) as src_dst:
                    image = src_dst.tile(
                        x,
                        y,
                        z,
                        tilesize=scale * 256,
                        **tile_params.as_dict(),
                        **layer_params.as_dict(),
                        **dataset_params.as_dict(),
                    )
                    dst_colormap = getattr(src_dst, "colormap", None)

            if post_process:
                image = post_process(image)

            content, media_type = self.render_func(
                image,
                output_format=format,
                colormap=colormap or dst_colormap,
                **render_params.as_dict(),
            )

            headers: dict[str, str] = {}
            if image.bounds is not None:
                headers["Content-Bbox"] = ",".join(map(str, image.bounds))
            if uri := CRS_to_uri(image.crs):
                headers["Content-Crs"] = f"<{uri}>"

            return Response(content, media_type=media_type, headers=headers)

    def tilejson(self):  # noqa: C901
        """Register /tilejson.json endpoint."""

        @self.router.get(
            "/{tileMatrixSetId}/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
            operation_id=f"{self.operation_prefix}getTileJSON",
        )
        def tilejson(
            request: Request,
            tileMatrixSetId: Annotated[
                Literal[tuple(self.supported_tms.list())],
                Path(
                    description="Identifier selecting one of the TileMatrixSetId supported."
                ),
            ],
            tile_format: Annotated[
                ImageType | None,
                Query(
                    description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
                ),
            ] = None,
            tile_scale: Annotated[
                int,
                Query(
                    gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
                ),
            ] = 1,
            minzoom: Annotated[
                int | None,
                Query(description="Overwrite default minzoom."),
            ] = None,
            maxzoom: Annotated[
                int | None,
                Query(description="Overwrite default maxzoom."),
            ] = None,
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            tile_params=Depends(self.tile_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            post_process=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return TileJSON document for a dataset."""
            route_params = {
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
                "scale": tile_scale,
                "tileMatrixSetId": tileMatrixSetId,
            }
            if tile_format:
                route_params["format"] = tile_format.value
            tiles_url = self.url_for(request, "tile", **route_params)

            qs_key_to_remove = [
                "tilematrixsetid",
                "tile_format",
                "tile_scale",
                "minzoom",
                "maxzoom",
            ]
            qs = [
                (key, value)
                for (key, value) in request.query_params._list
                if key.lower() not in qs_key_to_remove
            ]
            if qs:
                tiles_url += f"?{urlencode(qs)}"

            tms = self.supported_tms.get(tileMatrixSetId)
            with rasterio.Env(**env):
                logger.info(f"opening data with reader: {self.reader}")
                with self.reader(
                    src_path, tms=tms, **reader_params.as_dict()
                ) as src_dst:
                    return {
                        "bounds": src_dst.get_geographic_bounds(
                            tms.rasterio_geographic_crs
                        ),
                        "minzoom": minzoom if minzoom is not None else src_dst.minzoom,
                        "maxzoom": maxzoom if maxzoom is not None else src_dst.maxzoom,
                        "tiles": [tiles_url],
                        "attribution": os.environ.get("TITILER_DEFAULT_ATTRIBUTION"),
                    }

    def map_viewer(self):  # noqa: C901
        """Register /map.html endpoint."""

        @self.router.get(
            "/{tileMatrixSetId}/map.html",
            response_class=HTMLResponse,
            operation_id=f"{self.operation_prefix}getMapViewer",
        )
        def map_viewer(
            request: Request,
            tileMatrixSetId: Annotated[
                Literal[tuple(self.supported_tms.list())],
                Path(
                    description="Identifier selecting one of the TileMatrixSetId supported."
                ),
            ],
            tile_format: Annotated[
                ImageType | None,
                Query(
                    description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
                ),
            ] = None,
            tile_scale: Annotated[
                int,
                Query(
                    gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
                ),
            ] = 1,
            minzoom: Annotated[
                int | None,
                Query(description="Overwrite default minzoom."),
            ] = None,
            maxzoom: Annotated[
                int | None,
                Query(description="Overwrite default maxzoom."),
            ] = None,
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            tile_params=Depends(self.tile_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            post_process=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return TileJSON document for a dataset."""
            tilejson_url = self.url_for(
                request, "tilejson", tileMatrixSetId=tileMatrixSetId
            )
            point_url = self.url_for(request, "point", lon="{lon}", lat="{lat}")
            if request.query_params._list:
                params = f"?{urlencode(request.query_params._list)}"
                tilejson_url += params
                point_url += params

            tms = self.supported_tms.get(tileMatrixSetId)
            return self.templates.TemplateResponse(
                request,
                name="map.html",
                context={
                    "tilejson_endpoint": tilejson_url,
                    "point_endpoint": point_url,
                    "tms": tms,
                    "resolutions": [matrix.cellSize for matrix in tms],
                },
                media_type="text/html",
            )

    ############################################################################
    # /point
    ############################################################################
    def point(self):
        """Register /point endpoints."""

        @self.router.get(
            "/point/{lon},{lat}",
            response_model=Point,
            response_class=JSONResponse,
            responses={200: {"description": "Return a value for a point"}},
            operation_id=f"{self.operation_prefix}getDataForPoint",
        )
        def point(
            lon: Annotated[float, Path(description="Longitude")],
            lat: Annotated[float, Path(description="Latitude")],
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            coord_crs=Depends(CoordCRSParams),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Point value for a dataset."""
            with rasterio.Env(**env):
                logger.info(f"opening data with reader: {self.reader}")
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    pts = src_dst.point(
                        lon,
                        lat,
                        coord_crs=coord_crs or WGS84_CRS,
                        **layer_params.as_dict(),
                        **dataset_params.as_dict(),
                    )

            return {
                "coordinates": [lon, lat],
                "values": pts.array.tolist(),
                "band_names": pts.band_names,
                "band_descriptions": pts.band_descriptions,
            }

    ############################################################################
    # /preview (Optional)
    ############################################################################
    def preview(self):
        """Register /preview endpoint."""

        @self.router.get(
            "/preview",
            operation_id=f"{self.operation_prefix}getPreview",
            **img_endpoint_params,
        )
        @self.router.get(
            "/preview.{format}",
            operation_id=f"{self.operation_prefix}getPreviewWithFormat",
            **img_endpoint_params,
        )
        @self.router.get(
            "/preview/{width}x{height}.{format}",
            operation_id=f"{self.operation_prefix}getPreviewWithSizeAndFormat",
            **img_endpoint_params,
        )
        def preview(
            format: Annotated[
                ImageType | None,
                Field(
                    description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg)."
                ),
            ] = None,
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_preview_dependency),
            dst_crs=Depends(DstCRSParams),
            post_process=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create preview of a dataset."""
            with rasterio.Env(**env):
                logger.info(f"opening data with reader: {self.reader}")
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    image = src_dst.preview(
                        **layer_params.as_dict(),
                        **image_params.as_dict(exclude_none=False),
                        **dataset_params.as_dict(),
                        dst_crs=dst_crs,
                    )
                    dst_colormap = getattr(src_dst, "colormap", None)

            if post_process:
                image = post_process(image)

            content, media_type = self.render_func(
                image,
                output_format=format,
                colormap=colormap or dst_colormap,
                **render_params.as_dict(),
            )

            headers: dict[str, str] = {}
            if image.bounds is not None:
                headers["Content-Bbox"] = ",".join(map(str, image.bounds))
            if uri := CRS_to_uri(image.crs):
                headers["Content-Crs"] = f"<{uri}>"

            return Response(content, media_type=media_type, headers=headers)

    ############################################################################
    # /bbox and /feature (Optional)
    ############################################################################
    def part(self):  # noqa: C901
        """Register /bbox and `/feature` endpoints."""

        # GET endpoints
        @self.router.get(
            "/bbox/{minx},{miny},{maxx},{maxy}.{format}",
            operation_id=f"{self.operation_prefix}getDataForBoundingBoxWithFormat",
            **img_endpoint_params,
        )
        @self.router.get(
            "/bbox/{minx},{miny},{maxx},{maxy}/{width}x{height}.{format}",
            operation_id=f"{self.operation_prefix}getDataForBoundingBoxWithSizesAndFormat",
            **img_endpoint_params,
        )
        def bbox_image(
            minx: Annotated[float, Path(description="Bounding box min X")],
            miny: Annotated[float, Path(description="Bounding box min Y")],
            maxx: Annotated[float, Path(description="Bounding box max X")],
            maxy: Annotated[float, Path(description="Bounding box max Y")],
            format: Annotated[
                ImageType | None,
                Field(
                    description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
                ),
            ] = None,
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_part_dependency),
            dst_crs=Depends(DstCRSParams),
            coord_crs=Depends(CoordCRSParams),
            post_process=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create image from a bbox."""
            with rasterio.Env(**env):
                logger.info(f"opening data with reader: {self.reader}")
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    image = src_dst.part(
                        [minx, miny, maxx, maxy],
                        dst_crs=dst_crs,
                        bounds_crs=coord_crs or WGS84_CRS,
                        **layer_params.as_dict(),
                        **image_params.as_dict(),
                        **dataset_params.as_dict(),
                    )
                    dst_colormap = getattr(src_dst, "colormap", None)

            if post_process:
                image = post_process(image)

            content, media_type = self.render_func(
                image,
                output_format=format,
                colormap=colormap or dst_colormap,
                **render_params.as_dict(),
            )

            headers: dict[str, str] = {}
            if image.bounds is not None:
                headers["Content-Bbox"] = ",".join(map(str, image.bounds))
            if uri := CRS_to_uri(image.crs):
                headers["Content-Crs"] = f"<{uri}>"

            return Response(content, media_type=media_type, headers=headers)

        # POST endpoints
        @self.router.post(
            "/feature",
            operation_id=f"{self.operation_prefix}postDataForGeoJSON",
            **img_endpoint_params,
        )
        @self.router.post(
            "/feature.{format}",
            operation_id=f"{self.operation_prefix}postDataForGeoJSONWithFormat",
            **img_endpoint_params,
        )
        @self.router.post(
            "/feature/{width}x{height}.{format}",
            operation_id=f"{self.operation_prefix}postDataForGeoJSONWithSizesAndFormat",
            **img_endpoint_params,
        )
        def feature_image(
            geojson: Annotated[Feature, Body(description="GeoJSON Feature.")],
            format: Annotated[
                ImageType | None,
                Field(
                    description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg)."
                ),
            ] = None,
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_part_dependency),
            coord_crs=Depends(CoordCRSParams),
            dst_crs=Depends(DstCRSParams),
            post_process=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create image from a geojson feature."""
            with rasterio.Env(**env):
                logger.info(f"opening data with reader: {self.reader}")
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    image = src_dst.feature(
                        geojson.model_dump(exclude_none=True),
                        shape_crs=coord_crs or WGS84_CRS,
                        dst_crs=dst_crs,
                        **layer_params.as_dict(),
                        **image_params.as_dict(),
                        **dataset_params.as_dict(),
                    )
                    dst_colormap = getattr(src_dst, "colormap", None)

            if post_process:
                image = post_process(image)

            content, media_type = self.render_func(
                image,
                output_format=format,
                colormap=colormap or dst_colormap,
                **render_params.as_dict(),
            )

            headers: dict[str, str] = {}
            if image.bounds is not None:
                headers["Content-Bbox"] = ",".join(map(str, image.bounds))
            if uri := CRS_to_uri(image.crs):
                headers["Content-Crs"] = f"<{uri}>"

            return Response(content, media_type=media_type, headers=headers)

    ############################################################################
    # OGC Maps (Optional)
    ############################################################################
    def ogc_maps(self):  # noqa: C901
        """Register OGC Maps /map` endpoint."""

        self.conforms_to.update(
            {
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/core",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/crs",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/scaling",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/scaling/width-definition",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/scaling/height-definition",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/spatial-subsetting",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/spatial-subsetting/bbox-definition",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/spatial-subsetting/bbox-crs",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/spatial-subsetting/crs-curie",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/png",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/jpeg",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/tiff",
            }
        )

        # GET endpoints
        @self.router.get(
            "/map",
            operation_id=f"{self.operation_prefix}getMap",
            **img_endpoint_params,
        )
        def get_map(
            src_path=Depends(self.path_dependency),
            ogc_params=Depends(OGCMapsParams),
            reader_params=Depends(self.reader_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            post_process=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            env=Depends(self.environment_dependency),
        ) -> Response:
            """OGC Maps API."""
            with rasterio.Env(**env):
                logger.info(f"opening data with reader: {self.reader}")
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    if ogc_params.bbox is not None:
                        image = src_dst.part(
                            ogc_params.bbox,
                            dst_crs=ogc_params.crs or src_dst.crs,
                            bounds_crs=ogc_params.bbox_crs or WGS84_CRS,
                            width=ogc_params.width,
                            height=ogc_params.height,
                            max_size=ogc_params.max_size,
                            **layer_params.as_dict(),
                            **dataset_params.as_dict(),
                        )

                    else:
                        image = src_dst.preview(
                            width=ogc_params.width,
                            height=ogc_params.height,
                            max_size=ogc_params.max_size,
                            dst_crs=ogc_params.crs or src_dst.crs,
                            **layer_params.as_dict(),
                            **dataset_params.as_dict(),
                        )

                    dst_colormap = getattr(src_dst, "colormap", None)

            if post_process:
                image = post_process(image)

            content, media_type = self.render_func(
                image,
                output_format=ogc_params.format,
                colormap=colormap or dst_colormap,
                **render_params.as_dict(),
            )

            headers: dict[str, str] = {}
            if image.bounds is not None:
                headers["Content-Bbox"] = ",".join(map(str, image.bounds))
            if uri := CRS_to_uri(image.crs):
                headers["Content-Crs"] = f"<{uri}>"

            return Response(content, media_type=media_type, headers=headers)


@define(kw_only=True)
class MultiBaseTilerFactory(TilerFactory):
    """Custom Tiler Factory for MultiBaseReader classes.

    Note:
        To be able to use the rio_tiler.io.MultiBaseReader we need to be able to pass a `assets`
        argument to most of its methods. By using the `AssetsBidxExprParams` for the `layer_dependency`, the
        .tile(), .point(), .preview() and the .part() methods will receive assets, expression or indexes arguments.

        The rio_tiler.io.MultiBaseReader  `.info()` and `.metadata()` have `assets` as
        a requirement arguments (https://github.com/cogeotiff/rio-tiler/blob/main/rio_tiler/io/base.py#L365).
        This means we have to update the /info and /metadata endpoints in order to add the `assets` dependency.

    """

    reader: type[MultiBaseReader]  # type: ignore

    # Assets/Indexes/Expression dependency
    layer_dependency: type[DefaultDependency] = AssetsBidxExprParams

    # Assets dependency
    assets_dependency: type[DefaultDependency] = AssetsParams

    # Overwrite the `/info` endpoint to return the list of assets when no assets is passed.
    def info(self):
        """Register /info endpoint."""

        @self.router.get(
            "/info",
            response_model=MultiBaseInfo,
            response_model_exclude_none=True,
            response_class=JSONResponse,
            responses={
                200: {
                    "description": "Return dataset's basic info or the list of available assets."
                }
            },
            operation_id=f"{self.operation_prefix}getInfo",
        )
        def info(
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            asset_params=Depends(self.assets_dependency),
            env=Depends(self.environment_dependency),
        ) -> MultiBaseInfo:
            """Return dataset's basic info or the list of available assets."""
            with rasterio.Env(**env):
                logger.info(f"opening data with reader: {self.reader}")
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    return src_dst.info(**asset_params.as_dict())

        @self.router.get(
            "/info.geojson",
            response_model=MultiBaseInfoGeoJSON,
            response_model_exclude_none=True,
            response_class=GeoJSONResponse,
            responses={
                200: {
                    "content": {"application/geo+json": {}},
                    "description": "Return dataset's basic info as a GeoJSON feature.",
                }
            },
            operation_id=f"{self.operation_prefix}getInfoGeoJSON",
        )
        def info_geojson(
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            asset_params=Depends(self.assets_dependency),
            crs=Depends(CRSParams),
            env=Depends(self.environment_dependency),
        ) -> MultiBaseInfoGeoJSON:
            """Return dataset's basic info as a GeoJSON feature."""
            with rasterio.Env(**env):
                logger.info(f"opening data with reader: {self.reader}")
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    bounds = src_dst.get_geographic_bounds(crs or WGS84_CRS)
                    geometry = bounds_to_geometry(bounds)

                    return Feature(
                        type="Feature",
                        bbox=bounds,
                        geometry=geometry,
                        properties=src_dst.info(**asset_params.as_dict()),
                    )

        @self.router.get(
            "/assets",
            response_model=list[str],
            responses={200: {"description": "Return a list of supported assets."}},
            operation_id=f"{self.operation_prefix}getAssets",
        )
        def available_assets(
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return a list of supported assets."""
            with rasterio.Env(**env):
                logger.info(f"opening data with reader: {self.reader}")
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    return src_dst.assets

    # Overwrite the `/statistics` endpoint because the MultiBaseReader output model is different (Dict[str, Dict[str, BandStatistics]])
    # and MultiBaseReader.statistics() method also has `assets` arguments to defaults to the list of assets.
    def statistics(self):  # noqa: C901
        """Register /statistics endpoint."""

        # GET endpoint
        @self.router.get(
            "/asset_statistics",
            response_class=JSONResponse,
            response_model=MultiBaseStatistics,
            responses={
                200: {
                    "content": {"application/json": {}},
                    "description": "Return dataset's statistics.",
                }
            },
            operation_id=f"{self.operation_prefix}getAssetsStatistics",
        )
        def asset_statistics(
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            asset_params=Depends(AssetsBidxParams),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_preview_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Per Asset statistics"""
            with rasterio.Env(**env):
                logger.info(f"opening data with reader: {self.reader}")
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    return src_dst.statistics(
                        **asset_params.as_dict(),
                        **image_params.as_dict(exclude_none=False),
                        **dataset_params.as_dict(),
                        **stats_params.as_dict(),
                        hist_options=histogram_params.as_dict(),
                    )

        # MultiBaseReader merged statistics
        # https://github.com/cogeotiff/rio-tiler/blob/main/rio_tiler/io/base.py#L455-L468
        # GET endpoint
        @self.router.get(
            "/statistics",
            response_class=JSONResponse,
            response_model=Statistics,
            responses={
                200: {
                    "content": {"application/json": {}},
                    "description": "Return dataset's statistics.",
                }
            },
            operation_id=f"{self.operation_prefix}getStatistics",
        )
        def statistics(
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            layer_params=Depends(AssetsBidxExprParamsOptional),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_preview_dependency),
            post_process=Depends(self.process_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Merged assets statistics."""
            with rasterio.Env(**env):
                logger.info(f"opening data with reader: {self.reader}")
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    # Default to all available assets
                    if not layer_params.assets and not layer_params.expression:
                        layer_params.assets = src_dst.assets

                    image = src_dst.preview(
                        **layer_params.as_dict(),
                        **image_params.as_dict(),
                        **dataset_params.as_dict(),
                    )

                    if post_process:
                        image = post_process(image)

                    return image.statistics(
                        **stats_params.as_dict(),
                        hist_options=histogram_params.as_dict(),
                    )

        # POST endpoint
        @self.router.post(
            "/statistics",
            response_model=MultiBaseStatisticsGeoJSON,
            response_model_exclude_none=True,
            response_class=GeoJSONResponse,
            responses={
                200: {
                    "content": {"application/geo+json": {}},
                    "description": "Return dataset's statistics from feature or featureCollection.",
                }
            },
            operation_id=f"{self.operation_prefix}postStatisticsForGeoJSON",
        )
        def geojson_statistics(
            geojson: Annotated[
                FeatureCollection | Feature,
                Body(description="GeoJSON Feature or FeatureCollection."),
            ],
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            layer_params=Depends(AssetsBidxExprParamsOptional),
            dataset_params=Depends(self.dataset_dependency),
            coord_crs=Depends(CoordCRSParams),
            dst_crs=Depends(DstCRSParams),
            post_process=Depends(self.process_dependency),
            image_params=Depends(self.img_part_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Statistics from a geojson feature or featureCollection."""
            fc = geojson
            if isinstance(fc, Feature):
                fc = FeatureCollection(type="FeatureCollection", features=[geojson])

            with rasterio.Env(**env):
                logger.info(f"opening data with reader: {self.reader}")
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    # Default to all available assets
                    if not layer_params.assets and not layer_params.expression:
                        layer_params.assets = src_dst.assets

                    for feature in fc.features:
                        image = src_dst.feature(
                            feature.model_dump(exclude_none=True),
                            shape_crs=coord_crs or WGS84_CRS,
                            dst_crs=dst_crs,
                            align_bounds_with_dataset=True,
                            **layer_params.as_dict(),
                            **image_params.as_dict(),
                            **dataset_params.as_dict(),
                        )

                        if post_process:
                            image = post_process(image)

                        stats = image.statistics(
                            **stats_params.as_dict(),
                            hist_options=histogram_params.as_dict(),
                        )

                        feature.properties = feature.properties or {}
                        # NOTE: because we use `src_dst.feature` the statistics will be in form of
                        # `Dict[str, BandStatistics]` and not `Dict[str, Dict[str, BandStatistics]]`
                        feature.properties.update({"statistics": stats})

            return fc.features[0] if isinstance(geojson, Feature) else fc


@define(kw_only=True)
class MultiBandTilerFactory(TilerFactory):
    """Custom Tiler Factory for MultiBandReader classes.

    Note:
        To be able to use the rio_tiler.io.MultiBandReader we need to be able to pass a `bands`
        argument to most of its methods. By using the `BandsExprParams` for the `layer_dependency`, the
        .tile(), .point(), .preview() and the .part() methods will receive bands or expression arguments.

        The rio_tiler.io.MultiBandReader  `.info()` and `.metadata()` have `bands` as
        a requirement arguments (https://github.com/cogeotiff/rio-tiler/blob/main/rio_tiler/io/base.py#L775).
        This means we have to update the /info and /metadata endpoints in order to add the `bands` dependency.

        For implementation example see https://github.com/developmentseed/titiler-pds

    """

    reader: type[MultiBandReader]  # type: ignore

    # Assets/Expression dependency
    layer_dependency: type[DefaultDependency] = BandsExprParams

    # Bands dependency
    bands_dependency: type[DefaultDependency] = BandsParams

    def info(self):
        """Register /info endpoint."""

        @self.router.get(
            "/info",
            response_model=Info,
            response_model_exclude_none=True,
            response_class=JSONResponse,
            responses={200: {"description": "Return dataset's basic info."}},
            operation_id=f"{self.operation_prefix}getInfo",
        )
        def info(
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            bands_params=Depends(self.bands_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return dataset's basic info."""
            with rasterio.Env(**env):
                logger.info(f"opening data with reader: {self.reader}")
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    return src_dst.info(**bands_params.as_dict())

        @self.router.get(
            "/info.geojson",
            response_model=InfoGeoJSON,
            response_model_exclude_none=True,
            response_class=GeoJSONResponse,
            responses={
                200: {
                    "content": {"application/geo+json": {}},
                    "description": "Return dataset's basic info as a GeoJSON feature.",
                }
            },
            operation_id=f"{self.operation_prefix}getInfoGeoJSON",
        )
        def info_geojson(
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            bands_params=Depends(self.bands_dependency),
            crs=Depends(CRSParams),
            env=Depends(self.environment_dependency),
        ):
            """Return dataset's basic info as a GeoJSON feature."""
            with rasterio.Env(**env):
                logger.info(f"opening data with reader: {self.reader}")
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    bounds = src_dst.get_geographic_bounds(crs or WGS84_CRS)
                    geometry = bounds_to_geometry(bounds)

                    return Feature(
                        type="Feature",
                        bbox=bounds,
                        geometry=geometry,
                        properties=src_dst.info(**bands_params.as_dict()),
                    )

        @self.router.get(
            "/bands",
            response_model=list[str],
            responses={200: {"description": "Return a list of supported bands."}},
            operation_id=f"{self.operation_prefix}getBands",
        )
        def available_bands(
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return a list of supported bands."""
            with rasterio.Env(**env):
                logger.info(f"opening data with reader: {self.reader}")
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    return src_dst.bands

    # Overwrite the `/statistics` endpoint because we need bands to default to the list of bands.
    def statistics(self):  # noqa: C901
        """add statistics endpoints."""

        # GET endpoint
        @self.router.get(
            "/statistics",
            response_class=JSONResponse,
            response_model=Statistics,
            responses={
                200: {
                    "content": {"application/json": {}},
                    "description": "Return dataset's statistics.",
                }
            },
            operation_id=f"{self.operation_prefix}getStatistics",
        )
        def statistics(
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            bands_params=Depends(BandsExprParamsOptional),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_preview_dependency),
            post_process=Depends(self.process_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Dataset statistics."""
            with rasterio.Env(**env):
                logger.info(f"opening data with reader: {self.reader}")
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    # Default to all available bands
                    if not bands_params.bands and not bands_params.expression:
                        bands_params.bands = src_dst.bands

                    image = src_dst.preview(
                        **bands_params.as_dict(),
                        **image_params.as_dict(),
                        **dataset_params.as_dict(),
                    )

                    if post_process:
                        image = post_process(image)

                    return image.statistics(
                        **stats_params.as_dict(),
                        hist_options=histogram_params.as_dict(),
                    )

        # POST endpoint
        @self.router.post(
            "/statistics",
            response_model=StatisticsGeoJSON,
            response_model_exclude_none=True,
            response_class=GeoJSONResponse,
            responses={
                200: {
                    "content": {"application/geo+json": {}},
                    "description": "Return dataset's statistics from feature or featureCollection.",
                }
            },
            operation_id=f"{self.operation_prefix}postStatisticsForGeoJSON",
        )
        def geojson_statistics(
            geojson: Annotated[
                FeatureCollection | Feature,
                Body(description="GeoJSON Feature or FeatureCollection."),
            ],
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            bands_params=Depends(BandsExprParamsOptional),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_part_dependency),
            coord_crs=Depends(CoordCRSParams),
            dst_crs=Depends(DstCRSParams),
            post_process=Depends(self.process_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Statistics from a geojson feature or featureCollection."""
            fc = geojson
            if isinstance(fc, Feature):
                fc = FeatureCollection(type="FeatureCollection", features=[geojson])

            with rasterio.Env(**env):
                logger.info(f"opening data with reader: {self.reader}")
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    # Default to all available bands
                    if not bands_params.bands and not bands_params.expression:
                        bands_params.bands = src_dst.bands

                    for feature in fc.features:
                        image = src_dst.feature(
                            feature.model_dump(exclude_none=True),
                            shape_crs=coord_crs or WGS84_CRS,
                            dst_crs=dst_crs,
                            align_bounds_with_dataset=True,
                            **bands_params.as_dict(),
                            **image_params.as_dict(),
                            **dataset_params.as_dict(),
                        )

                        if post_process:
                            image = post_process(image)

                        stats = image.statistics(
                            **stats_params.as_dict(),
                            hist_options=histogram_params.as_dict(),
                        )

                        feature.properties = feature.properties or {}
                        feature.properties.update({"statistics": stats})

            return fc.features[0] if isinstance(geojson, Feature) else fc


@define(kw_only=True)
class TMSFactory(BaseFactory):
    """TileMatrixSet endpoints Factory."""

    supported_tms: TileMatrixSets = morecantile_tms

    def register_routes(self):
        """Register TMS endpoint routes."""

        @self.router.get(
            "/tileMatrixSets",
            response_model=TileMatrixSetList,
            response_model_exclude_none=True,
            summary="Retrieve the list of available tiling schemes (tile matrix sets).",
            operation_id=f"{self.operation_prefix}getTileMatrixSetsList",
            responses={
                200: {
                    "content": {
                        "application/json": {},
                        "text/html": {},
                    },
                },
            },
        )
        async def tilematrixsets(
            request: Request,
            f: Annotated[
                Literal["html", "json"] | None,
                Query(
                    description="Response MediaType. Defaults to endpoint's default or value defined in `accept` header."
                ),
            ] = None,
        ):
            """
            OGC Specification: http://docs.opengeospatial.org/per/19-069.html#_tilematrixsets
            """

            data = TileMatrixSetList(
                tileMatrixSets=[
                    {  # type: ignore
                        "id": tms_id,
                        "links": [
                            {
                                "href": self.url_for(
                                    request,
                                    "tilematrixset",
                                    tileMatrixSetId=tms_id,
                                ),
                                "rel": "http://www.opengis.net/def/rel/ogc/1.0/tiling-scheme",
                                "type": "application/json",
                                "title": f"Definition of {tms_id} tileMatrixSet",
                            }
                        ],
                    }
                    for tms_id in self.supported_tms.list()
                ]
            )

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
                    data.model_dump(exclude_none=True, mode="json"),
                    title="TileMatrixSets",
                    template_name="tilematrixsets",
                    templates=self.templates,
                )

            return data

        @self.router.get(
            "/tileMatrixSets/{tileMatrixSetId}",
            response_model=TileMatrixSet,
            response_model_exclude_none=True,
            summary="Retrieve the definition of the specified tiling scheme (tile matrix set).",
            operation_id=f"{self.operation_prefix}getTileMatrixSet",
            responses={
                200: {
                    "content": {
                        "application/json": {},
                        "text/html": {},
                    },
                },
            },
        )
        async def tilematrixset(
            request: Request,
            tileMatrixSetId: Annotated[
                Literal[tuple(self.supported_tms.list())],
                Path(description="Identifier for a supported TileMatrixSet."),
            ],
            f: Annotated[
                Literal["html", "json"] | None,
                Query(
                    description="Response MediaType. Defaults to endpoint's default or value defined in `accept` header."
                ),
            ] = None,
        ):
            """
            OGC Specification: http://docs.opengeospatial.org/per/19-069.html#_tilematrixset
            """
            tms = self.supported_tms.get(tileMatrixSetId)

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
                    {
                        **tms.model_dump(exclude_none=True, mode="json"),
                        # For visualization purpose we add the tms bbox
                        "bbox": list(tms.bbox),
                    },
                    title=f"{tileMatrixSetId} TileMatrixSet",
                    template_name="tilematrixset",
                    templates=self.templates,
                )

            return tms


@define(kw_only=True)
class AlgorithmFactory(BaseFactory):
    """Algorithm endpoints Factory."""

    # Supported algorithm
    supported_algorithm: Algorithms = available_algorithms

    def _get_algo_metadata(self, algorithm: type[BaseAlgorithm]) -> AlgorithmMetadata:
        """Algorithm Metadata"""
        props = algorithm.model_json_schema()["properties"]

        # title and description
        info = {
            k: v["default"]
            for k, v in props.items()
            if k == "title" or k == "description"
        }
        title = info.get("title", None)
        description = info.get("description", None)

        # Inputs Metadata
        ins = {
            k.replace("input_", ""): v["default"]
            for k, v in props.items()
            if k.startswith("input_") and "default" in v
        }

        # Output Metadata
        outs = {
            k.replace("output_", ""): v["default"]
            for k, v in props.items()
            if k.startswith("output_") and "default" in v
        }

        # Algorithm Parameters
        params = {
            k: v
            for k, v in props.items()
            if not k.startswith("input_")
            and not k.startswith("output_")
            and k != "title"
            and k != "description"
        }
        return AlgorithmMetadata(
            title=title,
            description=description,
            inputs=ins,
            outputs=outs,
            parameters=params,
        )

    def register_routes(self):
        """Register Algorithm routes."""

        @self.router.get(
            "/algorithms",
            response_model=AlgorithmtList,
            summary="Retrieve the list of available Algorithms.",
            operation_id=f"{self.operation_prefix}getAlgorithmList",
            responses={
                200: {
                    "content": {
                        "application/json": {},
                        "text/html": {},
                    },
                },
            },
        )
        def available_algorithms(
            request: Request,
            f: Annotated[
                Literal["html", "json"] | None,
                Query(
                    description="Response MediaType. Defaults to endpoint's default or value defined in `accept` header."
                ),
            ] = None,
        ):
            """Retrieve the list of available Algorithms."""
            data = AlgorithmtList(
                algorithms=[
                    {  # type: ignore
                        "id": algo_id,
                        "links": [
                            {
                                "href": self.url_for(
                                    request,
                                    "algorithm_metadata",
                                    algorithmId=algo_id,
                                ),
                                "rel": "item",
                                "type": "application/json",
                                "title": f"Definition of {algo_id} Algorithm",
                            }
                        ],
                    }
                    for algo_id, _ in self.supported_algorithm.data.items()
                ],
            )

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
                    data.model_dump(exclude_none=True, mode="json"),
                    title="Algorithms",
                    template_name="algorithms",
                    templates=self.templates,
                )

            return data

        @self.router.get(
            "/algorithms/{algorithmId}",
            response_model=AlgorithmMetadata,
            summary="Retrieve the metadata of the specified algorithm.",
            operation_id=f"{self.operation_prefix}getAlgorithm",
            responses={
                200: {
                    "content": {
                        "application/json": {},
                        "text/html": {},
                    },
                },
            },
        )
        def algorithm_metadata(
            request: Request,
            algorithmId: Annotated[
                Literal[tuple(self.supported_algorithm.list())],
                Path(description="Algorithm name"),
            ],
            f: Annotated[
                Literal["html", "json"] | None,
                Query(
                    description="Response MediaType. Defaults to endpoint's default or value defined in `accept` header."
                ),
            ] = None,
        ):
            """Retrieve the metadata of the specified algorithm."""
            data = self._get_algo_metadata(self.supported_algorithm.get(algorithmId))

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
                    data.model_dump(exclude_none=True, mode="json"),
                    title=f"{algorithmId} Algorithm",
                    template_name="algorithm",
                    templates=self.templates,
                )

            return data


@define(kw_only=True)
class ColorMapFactory(BaseFactory):
    """Colormap endpoints Factory."""

    # Supported colormaps
    supported_colormaps: ColorMaps = default_cmap

    def _image_from_colormap(
        self,
        cmap,
        orientation: Literal["vertical", "horizontal"] | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> ImageData:
        """Create an image from a colormap."""
        orientation = orientation or "horizontal"

        if isinstance(cmap, Sequence):
            values = [minv for ((minv, _), _) in cmap]
            arr = numpy.array([values] * 20)

            if orientation == "vertical":
                height = height or 256 if len(values) < 256 else len(values)
            else:
                width = width or 256 if len(values) < 256 else len(values)

        ###############################################################
        # DISCRETE CMAP
        elif len(cmap) != 256 or max(cmap) >= 256 or min(cmap) < 0:
            values = list(cmap)
            arr = numpy.array([values] * 20)

            if orientation == "vertical":
                height = height or 256 if len(values) < 256 else len(values)
            else:
                width = width or 256 if len(values) < 256 else len(values)

        ###############################################################
        # LINEAR CMAP
        else:
            cmin, cmax = min(cmap), max(cmap)
            arr = numpy.array(
                [numpy.round(numpy.linspace(cmin, cmax, num=256)).astype(numpy.uint8)]
                * 20
            )

        if orientation == "vertical":
            arr = arr.transpose([1, 0])

        img = ImageData(arr)

        width = width or img.width
        height = height or img.height
        if width != img.width or height != img.height:
            img = img.resize(height, width)

        return img

    def register_routes(self):  # noqa: C901
        """Register ColorMap routes."""

        @self.router.get(
            "/colorMaps",
            response_model=ColorMapList,
            response_model_exclude_none=True,
            summary="Retrieve the list of available colormaps.",
            operation_id=f"{self.operation_prefix}getColorMapList",
            responses={
                200: {
                    "content": {
                        "application/json": {},
                        "text/html": {},
                    },
                },
            },
        )
        def available_colormaps(
            request: Request,
            f: Annotated[
                Literal["html", "json"] | None,
                Query(
                    description="Response MediaType. Defaults to endpoint's default or value defined in `accept` header."
                ),
            ] = None,
        ):
            """Retrieve the list of available colormaps."""
            data = ColorMapList(
                colormaps=[
                    {  # type: ignore
                        "id": cmap_name,
                        "links": [
                            {
                                "href": self.url_for(
                                    request,
                                    "colormap_metadata",
                                    colorMapId=cmap_name,
                                ),
                                "rel": "item",
                                "type": "application/json",
                                "title": f"Definition of {cmap_name} ColorMap",
                            }
                        ],
                    }
                    for cmap_name in self.supported_colormaps.list()
                ],
            )

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
                    data.model_dump(exclude_none=True, mode="json"),
                    title="ColorMaps",
                    template_name="colormaps",
                    templates=self.templates,
                )

            return data

        @self.router.get(
            "/colorMaps/{colorMapId}",
            response_model=ColorMapType,
            summary="Retrieve the colorMap metadata or image.",
            operation_id=f"{self.operation_prefix}getColorMap",
            responses={
                200: {
                    "content": {
                        "application/json": {},
                        "image/png": {},
                        "image/jpeg": {},
                        "image/jpg": {},
                        "image/webp": {},
                        "image/jp2": {},
                        "image/tiff; application=geotiff": {},
                        "application/x-binary": {},
                        "text/html": {},
                    }
                },
            },
        )
        def colormap_metadata(  # noqa: C901
            request: Request,
            colorMapId: Annotated[
                Literal[tuple(self.supported_colormaps.list())],
                Path(description="ColorMap name"),
            ],
            f: Annotated[
                (
                    Literal[
                        "html",
                        "json",
                        "png",
                        "npy",
                        "tif",
                        "tiff",
                        "jpeg",
                        "jpg",
                        "jp2",
                        "webp",
                        "pngraw",
                    ]
                    | None
                ),
                Query(
                    description="Response MediaType. Defaults to endpoint's default or value defined in `accept` header."
                ),
            ] = None,
            orientation: Annotated[
                Literal["vertical", "horizontal"] | None,
                Query(
                    description="Image Orientation.",
                ),
            ] = None,
            height: Annotated[
                int | None,
                Query(
                    description="Image Height (default to 20px for horizontal or 256px for vertical).",
                ),
            ] = None,
            width: Annotated[
                int | None,
                Query(
                    description="Image Width (default to 256px for horizontal or 20px for vertical).",
                ),
            ] = None,
        ):
            """Retrieve the metadata of the specified colormap."""
            cmap = self.supported_colormaps.get(colorMapId)

            if f:
                output_type = MediaType[f]
            else:
                accepted_media = [MediaType.html, MediaType.json]
                output_type = (
                    accept_media_type(request.headers.get("accept", ""), accepted_media)
                    or MediaType.json
                )

            if output_type.name in [im.name for im in ImageType]:
                img = self._image_from_colormap(
                    cmap,
                    orientation,
                    width=width,
                    height=height,
                )

                format = ImageType[output_type.name]
                return Response(
                    img.render(img_format=format.driver, colormap=cmap),
                    media_type=format.mediatype,
                )

            elif output_type == MediaType.html:
                img = self._image_from_colormap(cmap, orientation="vertical")
                content = img.render(img_format="PNG", colormap=cmap)

                return create_html_response(
                    request,
                    base64.b64encode(content).decode(),
                    title=colorMapId,
                    template_name="colormap",
                    templates=self.templates,
                )

            data: ColorMapType
            if isinstance(cmap, Sequence):
                data = [(k, numpy.array(v).tolist()) for (k, v) in cmap]
            else:
                data = {k: numpy.array(v).tolist() for k, v in cmap.items()}

            return data
