"""TiTiler Router factories."""

import abc
import warnings
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
)
from urllib.parse import urlencode

import jinja2
import numpy
import rasterio
from fastapi import APIRouter, Body, Depends, Path, Query
from fastapi.dependencies.utils import get_parameterless_sub_dependant
from fastapi.params import Depends as DependsFunc
from geojson_pydantic.features import Feature, FeatureCollection
from geojson_pydantic.geometries import Polygon
from morecantile import TileMatrixSet
from morecantile import tms as morecantile_tms
from morecantile.defaults import TileMatrixSets
from pydantic import conint
from rio_tiler.colormap import ColorMaps
from rio_tiler.colormap import cmap as default_cmap
from rio_tiler.constants import WGS84_CRS
from rio_tiler.io import BaseReader, MultiBandReader, MultiBaseReader, Reader
from rio_tiler.models import Bounds, ImageData, Info
from rio_tiler.types import ColorMapType
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from starlette.routing import Match, compile_path, replace_params
from starlette.templating import Jinja2Templates
from typing_extensions import Annotated

from titiler.core.algorithm import AlgorithmMetadata, Algorithms, BaseAlgorithm
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
    ColorFormulaParams,
    ColorMapParams,
    CoordCRSParams,
    DatasetParams,
    DatasetPathParams,
    DefaultDependency,
    DstCRSParams,
    HistogramParams,
    ImageRenderingParams,
    PartFeatureParams,
    PreviewParams,
    RescaleType,
    RescalingParams,
    StatisticsParams,
    TileParams,
)
from titiler.core.models.mapbox import TileJSON
from titiler.core.models.OGC import TileMatrixSetList
from titiler.core.models.responses import (
    ColorMapsList,
    InfoGeoJSON,
    MultiBaseInfo,
    MultiBaseInfoGeoJSON,
    MultiBaseStatistics,
    MultiBaseStatisticsGeoJSON,
    Point,
    Statistics,
    StatisticsGeoJSON,
)
from titiler.core.resources.enums import ImageType, MediaType, OptionalHeader
from titiler.core.resources.responses import GeoJSONResponse, JSONResponse, XMLResponse
from titiler.core.routing import EndpointScope
from titiler.core.utils import render_image

jinja2_env = jinja2.Environment(
    loader=jinja2.ChoiceLoader([jinja2.PackageLoader(__package__, "templates")])
)
DEFAULT_TEMPLATES = Jinja2Templates(env=jinja2_env)

img_endpoint_params: Dict[str, Any] = {
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


@dataclass  # type: ignore
class FactoryExtension(metaclass=abc.ABCMeta):
    """Factory Extension."""

    @abc.abstractmethod
    def register(self, factory: "BaseTilerFactory"):
        """Register extension to the factory."""
        ...


# ref: https://github.com/python/mypy/issues/5374
@dataclass  # type: ignore
class BaseTilerFactory(metaclass=abc.ABCMeta):
    """BaseTiler Factory.

    Abstract Base Class which defines most inputs used by dynamic tiler.

    Attributes:
        reader (rio_tiler.io.base.BaseReader): A rio-tiler reader (e.g Reader).
        router (fastapi.APIRouter): Application router to register endpoints to.
        path_dependency (Callable): Endpoint dependency defining `path` to pass to the reader init.
        dataset_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining dataset overwriting options (e.g nodata).
        layer_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining dataset indexes/bands/assets options.
        render_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining image rendering options (e.g add_mask).
        colormap_dependency (Callable): Endpoint dependency defining ColorMap options (e.g colormap_name).
        process_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining image post-processing options (e.g rescaling, color-formula).
        tms_dependency (Callable): Endpoint dependency defining TileMatrixSet to use.
        reader_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining BaseReader options.
        environment_dependency (Callable): Endpoint dependency to define GDAL environment at runtime.
        router_prefix (str): prefix where the router will be mounted in the application.
        optional_headers(sequence of titiler.core.resources.enums.OptionalHeader): additional headers to return with the response.

    """

    reader: Type[BaseReader]

    # FastAPI router
    router: APIRouter = field(default_factory=APIRouter)

    # Path Dependency
    path_dependency: Callable[..., Any] = DatasetPathParams

    # Indexes/Expression Dependencies
    layer_dependency: Type[DefaultDependency] = BidxExprParams

    # Rasterio Dataset Options (nodata, unscale, resampling, reproject)
    dataset_dependency: Type[DefaultDependency] = DatasetParams

    # Post Processing Dependencies (algorithm)
    process_dependency: Callable[
        ..., Optional[BaseAlgorithm]
    ] = available_algorithms.dependency

    # Image rendering Dependencies
    rescale_dependency: Callable[..., Optional[RescaleType]] = RescalingParams
    color_formula_dependency: Callable[..., Optional[str]] = ColorFormulaParams
    colormap_dependency: Callable[..., Optional[ColorMapType]] = ColorMapParams
    render_dependency: Type[DefaultDependency] = ImageRenderingParams

    # Reader dependency
    reader_dependency: Type[DefaultDependency] = DefaultDependency

    # GDAL ENV dependency
    environment_dependency: Callable[..., Dict] = field(default=lambda: {})

    # TileMatrixSet dependency
    supported_tms: TileMatrixSets = morecantile_tms
    default_tms: Optional[str] = None

    # Router Prefix is needed to find the path for /tile if the TilerFactory.router is mounted
    # with other router (multiple `.../tile` routes).
    # e.g if you mount the route with `/cog` prefix, set router_prefix to cog and
    router_prefix: str = ""

    # add additional headers in response
    optional_headers: List[OptionalHeader] = field(default_factory=list)

    # add dependencies to specific routes
    route_dependencies: List[Tuple[List[EndpointScope], List[DependsFunc]]] = field(
        default_factory=list
    )

    extensions: List[FactoryExtension] = field(default_factory=list)

    templates: Jinja2Templates = DEFAULT_TEMPLATES

    def __post_init__(self):
        """Post Init: register route and configure specific options."""
        # TODO: remove this in 0.19
        if self.default_tms:
            warnings.warn(
                "`default_tms` attribute is deprecated and will be removed in 0.19.",
                DeprecationWarning,
            )

        self.default_tms = self.default_tms or "WebMercatorQuad"

        # Register endpoints
        self.register_routes()

        # Register Extensions
        for ext in self.extensions:
            ext.register(self)

        # Update endpoints dependencies
        for scopes, dependencies in self.route_dependencies:
            self.add_route_dependencies(scopes=scopes, dependencies=dependencies)

    @abc.abstractmethod
    def register_routes(self):
        """Register Tiler Routes."""
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
        scopes: List[EndpointScope],
        dependencies=List[DependsFunc],
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


@dataclass
class TilerFactory(BaseTilerFactory):
    """Tiler Factory.

    Attributes:
        reader (rio_tiler.io.base.BaseReader): A rio-tiler reader. Defaults to `rio_tiler.io.Reader`.
        stats_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining options for rio-tiler's statistics method.
        histogram_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining options for numpy's histogram method.
        img_preview_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining options for rio-tiler's preview method.
        img_part_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining options for rio-tiler's part/feature methods.
        add_preview (bool): add `/preview` endpoints. Defaults to True.
        add_part (bool): add `/bbox` and `/feature` endpoints. Defaults to True.
        add_viewer (bool): add `/map` endpoints. Defaults to True.

    """

    # Default reader is set to rio_tiler.io.Reader
    reader: Type[BaseReader] = Reader

    # Statistics/Histogram Dependencies
    stats_dependency: Type[DefaultDependency] = StatisticsParams
    histogram_dependency: Type[DefaultDependency] = HistogramParams

    # Crop/Preview endpoints Dependencies
    img_preview_dependency: Type[DefaultDependency] = PreviewParams
    img_part_dependency: Type[DefaultDependency] = PartFeatureParams

    # Tile/Tilejson/WMTS Dependencies
    tile_dependency: Type[DefaultDependency] = TileParams

    # Add/Remove some endpoints
    add_preview: bool = True
    add_part: bool = True
    add_viewer: bool = True

    def register_routes(self):
        """
        This Method register routes to the router.

        Because we wrap the endpoints in a class we cannot define the routes as
        methods (because of the self argument). The HACK is to define routes inside
        the class method and register them after the class initialization.

        """
        # Default Routes
        # (/bounds, /info, /statistics, /tile, /tilejson.json, /WMTSCapabilities.xml and /point)
        self.bounds()
        self.info()
        self.statistics()
        self.tile()
        self.tilejson()
        self.wmts()
        self.point()

        # Optional Routes
        if self.add_preview:
            self.preview()

        if self.add_part:
            self.part()

        if self.add_viewer:
            self.map_viewer()

    ############################################################################
    # /bounds
    ############################################################################
    def bounds(self):
        """Register /bounds endpoint."""

        @self.router.get(
            "/bounds",
            response_model=Bounds,
            responses={200: {"description": "Return dataset's bounds."}},
        )
        def bounds(
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return the bounds of the COG."""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    return {"bounds": src_dst.geographic_bounds}

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
        )
        def info_geojson(
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return dataset's basic info as a GeoJSON feature."""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    return Feature(
                        type="Feature",
                        geometry=Polygon.from_bounds(*src_dst.geographic_bounds),
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
        )
        def statistics(
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_preview_dependency),
            post_process=Depends(self.process_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            reader_params=Depends(self.reader_dependency),
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
        )
        def geojson_statistics(
            geojson: Annotated[
                Union[FeatureCollection, Feature],
                Body(description="GeoJSON Feature or FeatureCollection."),
            ],
            src_path=Depends(self.path_dependency),
            coord_crs=Depends(CoordCRSParams),
            dst_crs=Depends(DstCRSParams),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_part_dependency),
            post_process=Depends(self.process_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Statistics from a geojson feature or featureCollection."""
            fc = geojson
            if isinstance(fc, Feature):
                fc = FeatureCollection(type="FeatureCollection", features=[geojson])

            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    for feature in fc:
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
    # /tiles
    ############################################################################
    def tile(self):  # noqa: C901
        """Register /tiles endpoint."""

        @self.router.get(r"/tiles/{z}/{x}/{y}", **img_endpoint_params, deprecated=True)
        @self.router.get(
            r"/tiles/{z}/{x}/{y}.{format}", **img_endpoint_params, deprecated=True
        )
        @self.router.get(
            r"/tiles/{z}/{x}/{y}@{scale}x", **img_endpoint_params, deprecated=True
        )
        @self.router.get(
            r"/tiles/{z}/{x}/{y}@{scale}x.{format}",
            **img_endpoint_params,
            deprecated=True,
        )
        @self.router.get(r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(
            r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}.{format}", **img_endpoint_params
        )
        @self.router.get(
            r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x", **img_endpoint_params
        )
        @self.router.get(
            r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
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
                f"Identifier selecting one of the TileMatrixSetId supported (default: '{self.default_tms}')",
            ] = self.default_tms,
            scale: Annotated[
                conint(gt=0, le=4), "Tile size scale. 1=256x256, 2=512x512..."
            ] = 1,
            format: Annotated[
                ImageType,
                "Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
            ] = None,
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            tile_params=Depends(self.tile_dependency),
            post_process=Depends(self.process_dependency),
            rescale=Depends(self.rescale_dependency),
            color_formula=Depends(self.color_formula_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create map tile from a dataset."""
            tms = self.supported_tms.get(tileMatrixSetId)
            with rasterio.Env(**env):
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

            if rescale:
                image.rescale(rescale)

            if color_formula:
                image.apply_color_formula(color_formula)

            content, media_type = render_image(
                image,
                output_format=format,
                colormap=colormap or dst_colormap,
                **render_params.as_dict(),
            )

            return Response(content, media_type=media_type)

    def tilejson(self):  # noqa: C901
        """Register /tilejson.json endpoint."""

        @self.router.get(
            "/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
            deprecated=True,
        )
        @self.router.get(
            "/{tileMatrixSetId}/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        def tilejson(
            request: Request,
            tileMatrixSetId: Annotated[
                Literal[tuple(self.supported_tms.list())],
                f"Identifier selecting one of the TileMatrixSetId supported (default: '{self.default_tms}')",
            ] = self.default_tms,
            src_path=Depends(self.path_dependency),
            tile_format: Annotated[
                Optional[ImageType],
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
                Optional[int],
                Query(description="Overwrite default minzoom."),
            ] = None,
            maxzoom: Annotated[
                Optional[int],
                Query(description="Overwrite default maxzoom."),
            ] = None,
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            tile_params=Depends(self.tile_dependency),
            post_process=Depends(self.process_dependency),
            rescale=Depends(self.rescale_dependency),
            color_formula=Depends(self.color_formula_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            reader_params=Depends(self.reader_dependency),
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
                with self.reader(
                    src_path, tms=tms, **reader_params.as_dict()
                ) as src_dst:
                    return {
                        "bounds": src_dst.geographic_bounds,
                        "minzoom": minzoom if minzoom is not None else src_dst.minzoom,
                        "maxzoom": maxzoom if maxzoom is not None else src_dst.maxzoom,
                        "tiles": [tiles_url],
                    }

    def map_viewer(self):  # noqa: C901
        """Register /map endpoint."""

        @self.router.get("/map", response_class=HTMLResponse, deprecated=True)
        @self.router.get("/{tileMatrixSetId}/map", response_class=HTMLResponse)
        def map_viewer(
            request: Request,
            src_path=Depends(self.path_dependency),
            tileMatrixSetId: Annotated[
                Literal[tuple(self.supported_tms.list())],
                f"Identifier selecting one of the TileMatrixSetId supported (default: '{self.default_tms}')",
            ] = self.default_tms,
            tile_format: Annotated[
                Optional[ImageType],
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
                Optional[int],
                Query(description="Overwrite default minzoom."),
            ] = None,
            maxzoom: Annotated[
                Optional[int],
                Query(description="Overwrite default maxzoom."),
            ] = None,
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            tile_params=Depends(self.tile_dependency),
            post_process=Depends(self.process_dependency),
            rescale=Depends(self.rescale_dependency),
            color_formula=Depends(self.color_formula_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return TileJSON document for a dataset."""
            tilejson_url = self.url_for(
                request, "tilejson", tileMatrixSetId=tileMatrixSetId
            )
            if request.query_params._list:
                tilejson_url += f"?{urlencode(request.query_params._list)}"

            tms = self.supported_tms.get(tileMatrixSetId)
            return self.templates.TemplateResponse(
                request,
                name="map.html",
                context={
                    "tilejson_endpoint": tilejson_url,
                    "tms": tms,
                    "resolutions": [matrix.cellSize for matrix in tms],
                },
                media_type="text/html",
            )

    def wmts(self):  # noqa: C901
        """Register /wmts endpoint."""

        @self.router.get(
            "/WMTSCapabilities.xml", response_class=XMLResponse, deprecated=True
        )
        @self.router.get(
            "/{tileMatrixSetId}/WMTSCapabilities.xml", response_class=XMLResponse
        )
        def wmts(
            request: Request,
            tileMatrixSetId: Annotated[
                Literal[tuple(self.supported_tms.list())],
                f"Identifier selecting one of the TileMatrixSetId supported (default: '{self.default_tms}')",
            ] = self.default_tms,
            src_path=Depends(self.path_dependency),
            tile_format: Annotated[
                ImageType,
                Query(description="Output image type. Default is png."),
            ] = ImageType.png,
            tile_scale: Annotated[
                int,
                Query(
                    gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
                ),
            ] = 1,
            minzoom: Annotated[
                Optional[int],
                Query(description="Overwrite default minzoom."),
            ] = None,
            maxzoom: Annotated[
                Optional[int],
                Query(description="Overwrite default maxzoom."),
            ] = None,
            use_epsg: Annotated[
                bool,
                Query(
                    description="Use EPSG code, not opengis.net, for the ows:SupportedCRS in the TileMatrixSet (set to True to enable ArcMap compatability)"
                ),
            ] = False,
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            tile_params=Depends(self.tile_dependency),
            post_process=Depends(self.process_dependency),
            rescale=Depends(self.rescale_dependency),
            color_formula=Depends(self.color_formula_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """OGC WMTS endpoint."""
            route_params = {
                "z": "{TileMatrix}",
                "x": "{TileCol}",
                "y": "{TileRow}",
                "scale": tile_scale,
                "format": tile_format.value,
                "tileMatrixSetId": tileMatrixSetId,
            }
            tiles_url = self.url_for(request, "tile", **route_params)

            qs_key_to_remove = [
                "tilematrixsetid",
                "tile_format",
                "tile_scale",
                "minzoom",
                "maxzoom",
                "service",
                "use_epsg",
                "request",
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
                with self.reader(
                    src_path, tms=tms, **reader_params.as_dict()
                ) as src_dst:
                    bounds = src_dst.geographic_bounds
                    minzoom = minzoom if minzoom is not None else src_dst.minzoom
                    maxzoom = maxzoom if maxzoom is not None else src_dst.maxzoom

            tileMatrix = []
            for zoom in range(minzoom, maxzoom + 1):
                matrix = tms.matrix(zoom)
                tm = f"""
                        <TileMatrix>
                            <ows:Identifier>{matrix.id}</ows:Identifier>
                            <ScaleDenominator>{matrix.scaleDenominator}</ScaleDenominator>
                            <TopLeftCorner>{matrix.pointOfOrigin[0]} {matrix.pointOfOrigin[1]}</TopLeftCorner>
                            <TileWidth>{matrix.tileWidth}</TileWidth>
                            <TileHeight>{matrix.tileHeight}</TileHeight>
                            <MatrixWidth>{matrix.matrixWidth}</MatrixWidth>
                            <MatrixHeight>{matrix.matrixHeight}</MatrixHeight>
                        </TileMatrix>"""
                tileMatrix.append(tm)

            if use_epsg:
                supported_crs = f"EPSG:{tms.crs.to_epsg()}"
            else:
                supported_crs = tms.crs.srs

            return self.templates.TemplateResponse(
                request,
                name="wmts.xml",
                context={
                    "tiles_endpoint": tiles_url,
                    "bounds": bounds,
                    "tileMatrix": tileMatrix,
                    "tms": tms,
                    "supported_crs": supported_crs,
                    "title": src_path if isinstance(src_path, str) else "TiTiler",
                    "layer_name": "Dataset",
                    "media_type": tile_format.mediatype,
                },
                media_type=MediaType.xml.value,
            )

    ############################################################################
    # /point
    ############################################################################
    def point(self):
        """Register /point endpoints."""

        @self.router.get(
            r"/point/{lon},{lat}",
            response_model=Point,
            response_class=JSONResponse,
            responses={200: {"description": "Return a value for a point"}},
        )
        def point(
            lon: Annotated[float, Path(description="Longitude")],
            lat: Annotated[float, Path(description="Latitude")],
            src_path=Depends(self.path_dependency),
            coord_crs=Depends(CoordCRSParams),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Point value for a dataset."""

            with rasterio.Env(**env):
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
                "values": pts.data.tolist(),
                "band_names": pts.band_names,
            }

    ############################################################################
    # /preview (Optional)
    ############################################################################
    def preview(self):
        """Register /preview endpoint."""

        @self.router.get(r"/preview", **img_endpoint_params)
        @self.router.get(r"/preview.{format}", **img_endpoint_params)
        def preview(
            format: Annotated[
                ImageType,
                "Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
            ] = None,
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dst_crs=Depends(DstCRSParams),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_preview_dependency),
            post_process=Depends(self.process_dependency),
            rescale=Depends(self.rescale_dependency),
            color_formula=Depends(self.color_formula_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create preview of a dataset."""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    image = src_dst.preview(
                        **layer_params.as_dict(),
                        **image_params.as_dict(),
                        **dataset_params.as_dict(),
                        dst_crs=dst_crs,
                    )
                    dst_colormap = getattr(src_dst, "colormap", None)

            if post_process:
                image = post_process(image)

            if rescale:
                image.rescale(rescale)

            if color_formula:
                image.apply_color_formula(color_formula)

            content, media_type = render_image(
                image,
                output_format=format,
                colormap=colormap or dst_colormap,
                **render_params.as_dict(),
            )

            return Response(content, media_type=media_type)

    ############################################################################
    # /bbox and /feature (Optional)
    ############################################################################
    def part(self):  # noqa: C901
        """Register /bbox and `/feature` endpoints."""

        # GET endpoints
        @self.router.get(
            "/bbox/{minx},{miny},{maxx},{maxy}.{format}",
            **img_endpoint_params,
        )
        @self.router.get(
            "/bbox/{minx},{miny},{maxx},{maxy}/{width}x{height}.{format}",
            **img_endpoint_params,
        )
        def bbox_image(
            minx: Annotated[float, Path(description="Bounding box min X")],
            miny: Annotated[float, Path(description="Bounding box min Y")],
            maxx: Annotated[float, Path(description="Bounding box max X")],
            maxy: Annotated[float, Path(description="Bounding box max Y")],
            format: Annotated[
                ImageType,
                "Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
            ] = None,
            src_path=Depends(self.path_dependency),
            dst_crs=Depends(DstCRSParams),
            coord_crs=Depends(CoordCRSParams),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_part_dependency),
            post_process=Depends(self.process_dependency),
            rescale=Depends(self.rescale_dependency),
            color_formula=Depends(self.color_formula_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create image from a bbox."""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params) as src_dst:
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

            if rescale:
                image.rescale(rescale)

            if color_formula:
                image.apply_color_formula(color_formula)

            content, media_type = render_image(
                image,
                output_format=format,
                colormap=colormap or dst_colormap,
                **render_params.as_dict(),
            )

            return Response(content, media_type=media_type)

        # POST endpoints
        @self.router.post(
            "/feature",
            **img_endpoint_params,
        )
        @self.router.post(
            "/feature.{format}",
            **img_endpoint_params,
        )
        @self.router.post(
            "/feature/{width}x{height}.{format}",
            **img_endpoint_params,
        )
        def feature_image(
            geojson: Annotated[Feature, Body(description="GeoJSON Feature.")],
            format: Annotated[
                ImageType,
                "Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
            ] = None,
            src_path=Depends(self.path_dependency),
            coord_crs=Depends(CoordCRSParams),
            dst_crs=Depends(DstCRSParams),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_part_dependency),
            post_process=Depends(self.process_dependency),
            rescale=Depends(self.rescale_dependency),
            color_formula=Depends(self.color_formula_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create image from a geojson feature."""
            with rasterio.Env(**env):
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

            if rescale:
                image.rescale(rescale)

            if color_formula:
                image.apply_color_formula(color_formula)

            content, media_type = render_image(
                image,
                output_format=format,
                colormap=colormap or dst_colormap,
                **render_params.as_dict(),
            )

            return Response(content, media_type=media_type)


@dataclass
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

    reader: Type[MultiBaseReader]

    # Assets/Indexes/Expression dependency
    layer_dependency: Type[DefaultDependency] = AssetsBidxExprParams

    # Assets dependency
    assets_dependency: Type[DefaultDependency] = AssetsParams

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
        )
        def info(
            src_path=Depends(self.path_dependency),
            asset_params=Depends(self.assets_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return dataset's basic info or the list of available assets."""
            with rasterio.Env(**env):
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
        )
        def info_geojson(
            src_path=Depends(self.path_dependency),
            asset_params=Depends(self.assets_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return dataset's basic info as a GeoJSON feature."""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    return Feature(
                        type="Feature",
                        geometry=Polygon.from_bounds(*src_dst.geographic_bounds),
                        properties={
                            asset: asset_info
                            for asset, asset_info in src_dst.info(
                                **asset_params.as_dict()
                            ).items()
                        },
                    )

        @self.router.get(
            "/assets",
            response_model=List[str],
            responses={200: {"description": "Return a list of supported assets."}},
        )
        def available_assets(
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return a list of supported assets."""
            with rasterio.Env(**env):
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
        )
        def asset_statistics(
            src_path=Depends(self.path_dependency),
            asset_params=Depends(AssetsBidxParams),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_preview_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Per Asset statistics"""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    return src_dst.statistics(
                        **asset_params.as_dict(),
                        **image_params.as_dict(),
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
        )
        def statistics(
            src_path=Depends(self.path_dependency),
            layer_params=Depends(AssetsBidxExprParamsOptional),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_preview_dependency),
            post_process=Depends(self.process_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Merged assets statistics."""
            with rasterio.Env(**env):
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
        )
        def geojson_statistics(
            geojson: Annotated[
                Union[FeatureCollection, Feature],
                Body(description="GeoJSON Feature or FeatureCollection."),
            ],
            src_path=Depends(self.path_dependency),
            coord_crs=Depends(CoordCRSParams),
            dst_crs=Depends(DstCRSParams),
            layer_params=Depends(AssetsBidxExprParamsOptional),
            dataset_params=Depends(self.dataset_dependency),
            post_process=Depends(self.process_dependency),
            image_params=Depends(self.img_part_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Statistics from a geojson feature or featureCollection."""
            fc = geojson
            if isinstance(fc, Feature):
                fc = FeatureCollection(type="FeatureCollection", features=[geojson])

            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    # Default to all available assets
                    if not layer_params.assets and not layer_params.expression:
                        layer_params.assets = src_dst.assets

                    for feature in fc:
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


@dataclass
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

    reader: Type[MultiBandReader]

    # Assets/Expression dependency
    layer_dependency: Type[DefaultDependency] = BandsExprParams

    # Bands dependency
    bands_dependency: Type[DefaultDependency] = BandsParams

    def info(self):
        """Register /info endpoint."""

        @self.router.get(
            "/info",
            response_model=Info,
            response_model_exclude_none=True,
            response_class=JSONResponse,
            responses={200: {"description": "Return dataset's basic info."}},
        )
        def info(
            src_path=Depends(self.path_dependency),
            bands_params=Depends(self.bands_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return dataset's basic info."""
            with rasterio.Env(**env):
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
        )
        def info_geojson(
            src_path=Depends(self.path_dependency),
            bands_params=Depends(self.bands_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return dataset's basic info as a GeoJSON feature."""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    return Feature(
                        type="Feature",
                        geometry=Polygon.from_bounds(*src_dst.geographic_bounds),
                        properties=src_dst.info(**bands_params.as_dict()),
                    )

        @self.router.get(
            "/bands",
            response_model=List[str],
            responses={200: {"description": "Return a list of supported bands."}},
        )
        def available_bands(
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return a list of supported bands."""
            with rasterio.Env(**env):
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
        )
        def statistics(
            src_path=Depends(self.path_dependency),
            bands_params=Depends(BandsExprParamsOptional),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_preview_dependency),
            post_process=Depends(self.process_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Dataset statistics."""
            with rasterio.Env(**env):
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
        )
        def geojson_statistics(
            geojson: Annotated[
                Union[FeatureCollection, Feature],
                Body(description="GeoJSON Feature or FeatureCollection."),
            ],
            src_path=Depends(self.path_dependency),
            coord_crs=Depends(CoordCRSParams),
            dst_crs=Depends(DstCRSParams),
            bands_params=Depends(BandsExprParamsOptional),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_part_dependency),
            post_process=Depends(self.process_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Statistics from a geojson feature or featureCollection."""
            fc = geojson
            if isinstance(fc, Feature):
                fc = FeatureCollection(type="FeatureCollection", features=[geojson])

            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    # Default to all available bands
                    if not bands_params.bands and not bands_params.expression:
                        bands_params.bands = src_dst.bands

                    for feature in fc:
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


@dataclass
class TMSFactory:
    """TileMatrixSet endpoints Factory."""

    supported_tms: TileMatrixSets = morecantile_tms

    # FastAPI router
    router: APIRouter = field(default_factory=APIRouter)

    # Router Prefix is needed to find the path for /tile if the TilerFactory.router is mounted
    # with other router (multiple `.../tile` routes).
    # e.g if you mount the route with `/cog` prefix, set router_prefix to cog and
    router_prefix: str = ""

    def __post_init__(self):
        """Post Init: register route and configure specific options."""
        self.register_routes()

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

    def register_routes(self):
        """Register TMS endpoint routes."""

        @self.router.get(
            r"/tileMatrixSets",
            response_model=TileMatrixSetList,
            response_model_exclude_none=True,
            summary="Retrieve the list of available tiling schemes (tile matrix sets).",
            operation_id="getTileMatrixSetsList",
            responses={
                200: {
                    "content": {
                        MediaType.json.value: {},
                    },
                },
            },
        )
        async def tilematrixsets(request: Request):
            """
            OGC Specification: http://docs.opengeospatial.org/per/19-069.html#_tilematrixsets
            """
            data = TileMatrixSetList(
                tileMatrixSets=[
                    {
                        "id": tms_id,
                        "links": [
                            {
                                "href": self.url_for(
                                    request,
                                    "tilematrixset",
                                    tileMatrixSetId=tms_id,
                                ),
                                "rel": "http://www.opengis.net/def/rel/ogc/1.0/tiling-schemes",
                                "type": "application/json",
                                "title": f"Definition of {tms_id} tileMatrixSet",
                            }
                        ],
                    }
                    for tms_id in self.supported_tms.list()
                ]
            )

            return data

        @self.router.get(
            "/tileMatrixSets/{tileMatrixSetId}",
            response_model=TileMatrixSet,
            response_model_exclude_none=True,
            summary="Retrieve the definition of the specified tiling scheme (tile matrix set).",
            operation_id="getTileMatrixSet",
            responses={
                200: {
                    "content": {
                        MediaType.json.value: {},
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
        ):
            """
            OGC Specification: http://docs.opengeospatial.org/per/19-069.html#_tilematrixset
            """
            return self.supported_tms.get(tileMatrixSetId)


@dataclass
class AlgorithmFactory:
    """Algorithm endpoints Factory."""

    # Supported algorithm
    supported_algorithm: Algorithms = available_algorithms

    # FastAPI router
    router: APIRouter = field(default_factory=APIRouter)

    def __post_init__(self):
        """Post Init: register routes"""

        def metadata(algorithm: BaseAlgorithm) -> AlgorithmMetadata:
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

        @self.router.get(
            "/algorithms",
            response_model=Dict[str, AlgorithmMetadata],
            summary="Retrieve the list of available Algorithms.",
            operation_id="getAlgorithms",
        )
        def available_algorithms(request: Request):
            """Retrieve the list of available Algorithms."""
            return {k: metadata(v) for k, v in self.supported_algorithm.data.items()}

        @self.router.get(
            "/algorithms/{algorithmId}",
            response_model=AlgorithmMetadata,
            summary="Retrieve the metadata of the specified algorithm.",
            operation_id="getAlgorithm",
        )
        def algorithm_metadata(
            algorithm: Annotated[
                Literal[tuple(self.supported_algorithm.list())],
                Path(description="Algorithm name", alias="algorithmId"),
            ],
        ):
            """Retrieve the metadata of the specified algorithm."""
            return metadata(self.supported_algorithm.get(algorithm))


@dataclass
class ColorMapFactory:
    """Colormap endpoints Factory."""

    # Supported colormaps
    supported_colormaps: ColorMaps = default_cmap

    # FastAPI router
    router: APIRouter = field(default_factory=APIRouter)

    def url_for(self, request: Request, name: str, **path_params: Any) -> str:
        """Return full url (with prefix) for a specific endpoint."""
        url_path = self.router.url_path_for(name, **path_params)
        base_url = str(request.base_url)
        return str(url_path.make_absolute_url(base_url=base_url))

    def __post_init__(self):  # noqa: C901
        """Post Init: register routes"""

        @self.router.get(
            "/colorMaps",
            response_model=ColorMapsList,
            response_model_exclude_none=True,
            summary="Retrieve the list of available colormaps.",
            operation_id="getColorMaps",
        )
        def available_colormaps(request: Request):
            """Retrieve the list of available colormaps."""
            return {
                "colorMaps": self.supported_colormaps.list(),
                "links": [
                    {
                        "title": "List of available colormaps",
                        "href": self.url_for(
                            request,
                            "available_colormaps",
                        ),
                        "type": "application/json",
                        "rel": "self",
                    },
                    {
                        "title": "Retrieve colorMap metadata",
                        "href": self.url_for(
                            request, "colormap_metadata", colorMapId="{colorMapId}"
                        ),
                        "type": "application/json",
                        "rel": "data",
                        "templated": True,
                    },
                    {
                        "title": "Retrieve colorMap as image",
                        "href": self.url_for(
                            request, "colormap_metadata", colorMapId="{colorMapId}"
                        )
                        + "?format=png",
                        "type": "image/png",
                        "rel": "data",
                        "templated": True,
                    },
                ],
            }

        @self.router.get(
            "/colorMaps/{colorMapId}",
            response_model=ColorMapType,
            summary="Retrieve the colorMap metadata or image.",
            operation_id="getColorMap",
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
                    }
                },
            },
        )
        def colormap_metadata(
            colormap: Annotated[
                Literal[tuple(self.supported_colormaps.list())],
                Path(description="ColorMap name", alias="colorMapId"),
            ],
            # Image Output Options
            format: Annotated[
                Optional[ImageType],
                Query(
                    description="Return colorMap as Image.",
                ),
            ] = None,
            orientation: Annotated[
                Optional[Literal["vertical", "horizontal"]],
                Query(
                    description="Image Orientation.",
                ),
            ] = None,
            height: Annotated[
                Optional[int],
                Query(
                    description="Image Height (default to 20px for horizontal or 256px for vertical).",
                ),
            ] = None,
            width: Annotated[
                Optional[int],
                Query(
                    description="Image Width (default to 256px for horizontal or 20px for vertical).",
                ),
            ] = None,
        ):
            """Retrieve the metadata of the specified colormap."""
            cmap = self.supported_colormaps.get(colormap)

            if format:
                ###############################################################
                # SEQUENCE CMAP
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
                        [
                            numpy.round(numpy.linspace(cmin, cmax, num=256)).astype(
                                numpy.uint8
                            )
                        ]
                        * 20
                    )

                if orientation == "vertical":
                    arr = arr.transpose([1, 0])

                img = ImageData(arr)

                width = width or img.width
                height = height or img.height
                if width != img.width or height != img.height:
                    img = img.resize(height, width)

                return Response(
                    img.render(img_format=format.driver, colormap=cmap),
                    media_type=format.mediatype,
                )

            if isinstance(cmap, Sequence):
                return [(k, numpy.array(v).tolist()) for (k, v) in cmap]
            else:
                return {k: numpy.array(v).tolist() for k, v in cmap.items()}
