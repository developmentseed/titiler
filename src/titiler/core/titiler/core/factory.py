"""TiTiler Router factories."""
import abc
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Type, Union
from urllib.parse import urlencode

import rasterio
from geojson_pydantic.features import Feature, FeatureCollection
from geojson_pydantic.geometries import Polygon
from morecantile import TileMatrixSet
from morecantile import tms as morecantile_tms
from morecantile.defaults import TileMatrixSets
from rio_tiler.io import BaseReader, MultiBandReader, MultiBaseReader, Reader
from rio_tiler.models import BandStatistics, Bounds, Info
from rio_tiler.types import ColorMapType
from rio_tiler.utils import get_array_statistics

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
    ColorMapParams,
    DatasetParams,
    DatasetPathParams,
    DefaultDependency,
    HistogramParams,
    ImageParams,
    ImageRenderingParams,
    RescalingParams,
    StatisticsParams,
)
from titiler.core.models.mapbox import TileJSON
from titiler.core.models.OGC import TileMatrixSetList
from titiler.core.models.responses import (
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

from fastapi import APIRouter, Body, Depends, Path, Query, params
from fastapi.dependencies.utils import get_parameterless_sub_dependant

from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from starlette.routing import Match
from starlette.templating import Jinja2Templates

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore

# TODO: mypy fails in python 3.9, we need to find a proper way to do this
templates = Jinja2Templates(directory=str(resources_files(__package__) / "templates"))  # type: ignore


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

    # Rasterio Dataset Options (nodata, unscale, resampling)
    dataset_dependency: Type[DefaultDependency] = DatasetParams

    # Indexes/Expression Dependencies
    layer_dependency: Type[DefaultDependency] = BidxExprParams

    # Image rendering Dependencies
    render_dependency: Type[DefaultDependency] = ImageRenderingParams
    colormap_dependency: Callable[..., Optional[ColorMapType]] = ColorMapParams

    # Post Processing Dependencies (algorithm)
    process_dependency: Callable[
        ..., Optional[BaseAlgorithm]
    ] = available_algorithms.dependency

    # Reader dependency
    reader_dependency: Type[DefaultDependency] = DefaultDependency

    # GDAL ENV dependency
    environment_dependency: Callable[..., Dict] = lambda: dict()

    # TileMatrixSet dependency
    supported_tms: TileMatrixSets = morecantile_tms
    default_tms: str = "WebMercatorQuad"

    # Router Prefix is needed to find the path for /tile if the TilerFactory.router is mounted
    # with other router (multiple `.../tile` routes).
    # e.g if you mount the route with `/cog` prefix, set router_prefix to cog and
    router_prefix: str = ""

    # add additional headers in response
    optional_headers: List[OptionalHeader] = field(default_factory=list)

    # add dependencies to specific routes
    route_dependencies: List[Tuple[List[EndpointScope], List[params.Depends]]] = field(
        default_factory=list
    )

    def __post_init__(self):
        """Post Init: register route and configure specific options."""
        self.register_routes()

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
            base_url += self.router_prefix.lstrip("/")
        return url_path.make_absolute_url(base_url=base_url)

    def add_route_dependencies(
        self,
        *,
        scopes: List[EndpointScope],
        dependencies=List[params.Depends],
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
                            depends=depends, path=route.path_format  # type: ignore
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
        img_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining options for rio-tiler's preview/crop method.
        add_preview (bool): add `/preview` endpoints. Defaults to True.
        add_part (bool): add `/crop` endpoints. Defaults to True.
        add_viewer (bool): add `/map` endpoints. Defaults to True.

    """

    # Default reader is set to rio_tiler.io.Reader
    reader: Type[BaseReader] = Reader

    # Statistics/Histogram Dependencies
    stats_dependency: Type[DefaultDependency] = StatisticsParams
    histogram_dependency: Type[DefaultDependency] = HistogramParams

    # Crop/Preview endpoints Dependencies
    img_dependency: Type[DefaultDependency] = ImageParams

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
                with self.reader(src_path, **reader_params) as src_dst:
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
                with self.reader(src_path, **reader_params) as src_dst:
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
                with self.reader(src_path, **reader_params) as src_dst:
                    return Feature(
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
            image_params=Depends(self.img_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Dataset statistics."""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params) as src_dst:
                    return src_dst.statistics(
                        **layer_params,
                        **image_params,
                        **dataset_params,
                        **stats_params,
                        hist_options={**histogram_params},
                    )

        # POST endpoint
        @self.router.post(
            "/statistics",
            response_model=StatisticsGeoJSON,
            response_model_exclude_none=True,
            response_class=GeoJSONResponse,
            responses={
                200: {
                    "content": {"application/json": {}},
                    "description": "Return dataset's statistics.",
                }
            },
        )
        def geojson_statistics(
            geojson: Union[FeatureCollection, Feature] = Body(
                ..., description="GeoJSON Feature or FeatureCollection."
            ),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Statistics from a geojson feature or featureCollection."""
            fc = geojson
            if isinstance(fc, Feature):
                fc = FeatureCollection(features=[geojson])

            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params) as src_dst:
                    for feature in fc:
                        data = src_dst.feature(
                            feature.dict(exclude_none=True),
                            **layer_params,
                            **image_params,
                            **dataset_params,
                        )
                        stats = get_array_statistics(
                            data.as_masked(),
                            **stats_params,
                            **histogram_params,
                        )

                        feature.properties = feature.properties or {}
                        feature.properties.update(
                            {
                                "statistics": {
                                    f"{data.band_names[ix]}": BandStatistics(
                                        **stats[ix]
                                    )
                                    for ix in range(len(stats))
                                }
                            }
                        )

            return fc.features[0] if isinstance(geojson, Feature) else fc

    ############################################################################
    # /tiles
    ############################################################################
    def tile(self):  # noqa: C901
        """Register /tiles endpoint."""

        @self.router.get(r"/tiles/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}.{format}", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}@{scale}x", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}@{scale}x.{format}", **img_endpoint_params)
        @self.router.get(r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}.{format}", **img_endpoint_params
        )
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x", **img_endpoint_params
        )
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
            **img_endpoint_params,
        )
        def tile(
            z: int = Path(..., ge=0, le=30, description="TMS tiles's zoom level"),
            x: int = Path(..., description="TMS tiles's column"),
            y: int = Path(..., description="TMS tiles's row"),
            TileMatrixSetId: Literal[tuple(self.supported_tms.list())] = Query(
                self.default_tms,
                description=f"TileMatrixSet Name (default: '{self.default_tms}')",
            ),
            scale: int = Query(
                1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
            ),
            format: ImageType = Query(
                None, description="Output image type. Default is auto."
            ),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            buffer: Optional[float] = Query(
                None,
                gt=0,
                title="Tile buffer.",
                description="Buffer on each side of the given tile. It must be a multiple of `0.5`. Output **tilesize** will be expanded to `tilesize + 2 * buffer` (e.g 0.5 = 257x257, 1.0 = 258x258).",
            ),
            post_process=Depends(self.process_dependency),
            rescale: Optional[List[Tuple[float, ...]]] = Depends(RescalingParams),
            color_formula: Optional[str] = Query(
                None,
                title="Color Formula",
                description="rio-color formula (info: https://github.com/mapbox/rio-color)",
            ),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create map tile from a dataset."""
            tms = self.supported_tms.get(TileMatrixSetId)
            with rasterio.Env(**env):
                with self.reader(src_path, tms=tms, **reader_params) as src_dst:
                    image = src_dst.tile(
                        x,
                        y,
                        z,
                        tilesize=scale * 256,
                        buffer=buffer,
                        **layer_params,
                        **dataset_params,
                    )
                    dst_colormap = getattr(src_dst, "colormap", None)

            if post_process:
                image = post_process(image)

            if rescale:
                image.rescale(rescale)

            if color_formula:
                image.apply_color_formula(color_formula)

            if not format:
                format = ImageType.jpeg if image.mask.all() else ImageType.png

            content = image.render(
                img_format=format.driver,
                colormap=colormap or dst_colormap,
                **format.profile,
                **render_params,
            )

            return Response(content, media_type=format.mediatype)

    def tilejson(self):  # noqa: C901
        """Register /tilejson.json endpoint."""

        @self.router.get(
            "/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        @self.router.get(
            "/{TileMatrixSetId}/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        def tilejson(
            request: Request,
            TileMatrixSetId: Literal[tuple(self.supported_tms.list())] = Query(
                self.default_tms,
                description=f"TileMatrixSet Name (default: '{self.default_tms}')",
            ),
            src_path=Depends(self.path_dependency),
            tile_format: Optional[ImageType] = Query(
                None, description="Output image type. Default is auto."
            ),
            tile_scale: int = Query(
                1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
            ),
            minzoom: Optional[int] = Query(
                None, description="Overwrite default minzoom."
            ),
            maxzoom: Optional[int] = Query(
                None, description="Overwrite default maxzoom."
            ),
            layer_params=Depends(self.layer_dependency),  # noqa
            dataset_params=Depends(self.dataset_dependency),  # noqa
            buffer: Optional[float] = Query(  # noqa
                None,
                gt=0,
                title="Tile buffer.",
                description="Buffer on each side of the given tile. It must be a multiple of `0.5`. Output **tilesize** will be expanded to `tilesize + 2 * buffer` (e.g 0.5 = 257x257, 1.0 = 258x258).",
            ),
            post_process=Depends(self.process_dependency),  # noqa
            rescale: Optional[List[Tuple[float, ...]]] = Depends(
                RescalingParams
            ),  # noqa
            color_formula: Optional[str] = Query(  # noqa
                None,
                title="Color Formula",
                description="rio-color formula (info: https://github.com/mapbox/rio-color)",
            ),
            colormap=Depends(self.colormap_dependency),  # noqa
            render_params=Depends(self.render_dependency),  # noqa
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return TileJSON document for a dataset."""
            route_params = {
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
                "scale": tile_scale,
                "TileMatrixSetId": TileMatrixSetId,
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

            tms = self.supported_tms.get(TileMatrixSetId)
            with rasterio.Env(**env):
                with self.reader(src_path, tms=tms, **reader_params) as src_dst:
                    return {
                        "bounds": src_dst.geographic_bounds,
                        "minzoom": minzoom if minzoom is not None else src_dst.minzoom,
                        "maxzoom": maxzoom if maxzoom is not None else src_dst.maxzoom,
                        "tiles": [tiles_url],
                    }

    def map_viewer(self):  # noqa: C901
        """Register /map endpoint."""

        @self.router.get("/map", response_class=HTMLResponse)
        @self.router.get("/{TileMatrixSetId}/map", response_class=HTMLResponse)
        def map_viewer(
            request: Request,
            src_path=Depends(self.path_dependency),
            TileMatrixSetId: Literal["WebMercatorQuad"] = Query(
                "WebMercatorQuad",
                description="TileMatrixSet Name (default: 'WebMercatorQuad')",
            ),  # noqa
            tile_format: Optional[ImageType] = Query(
                None, description="Output image type. Default is auto."
            ),  # noqa
            tile_scale: int = Query(
                1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
            ),  # noqa
            minzoom: Optional[int] = Query(
                None, description="Overwrite default minzoom."
            ),  # noqa
            maxzoom: Optional[int] = Query(
                None, description="Overwrite default maxzoom."
            ),  # noqa
            layer_params=Depends(self.layer_dependency),  # noqa
            dataset_params=Depends(self.dataset_dependency),  # noqa
            buffer: Optional[float] = Query(  # noqa
                None,
                gt=0,
                title="Tile buffer.",
                description="Buffer on each side of the given tile. It must be a multiple of `0.5`. Output **tilesize** will be expanded to `tilesize + 2 * buffer` (e.g 0.5 = 257x257, 1.0 = 258x258).",
            ),
            post_process=Depends(self.process_dependency),  # noqa
            rescale: Optional[List[Tuple[float, ...]]] = Depends(
                RescalingParams
            ),  # noqa
            color_formula: Optional[str] = Query(  # noqa
                None,
                title="Color Formula",
                description="rio-color formula (info: https://github.com/mapbox/rio-color)",
            ),
            colormap=Depends(self.colormap_dependency),  # noqa
            render_params=Depends(self.render_dependency),  # noqa
            reader_params=Depends(self.reader_dependency),  # noqa
            env=Depends(self.environment_dependency),  # noqa
        ):
            """Return TileJSON document for a dataset."""
            tilejson_url = self.url_for(request, "tilejson")
            if request.query_params._list:
                tilejson_url += f"?{urlencode(request.query_params._list)}"

            return templates.TemplateResponse(
                name="index.html",
                context={
                    "request": request,
                    "tilejson_endpoint": tilejson_url,
                },
                media_type="text/html",
            )

    def wmts(self):  # noqa: C901
        """Register /wmts endpoint."""

        @self.router.get("/WMTSCapabilities.xml", response_class=XMLResponse)
        @self.router.get(
            "/{TileMatrixSetId}/WMTSCapabilities.xml", response_class=XMLResponse
        )
        def wmts(
            request: Request,
            TileMatrixSetId: Literal[tuple(self.supported_tms.list())] = Query(
                self.default_tms,
                description=f"TileMatrixSet Name (default: '{self.default_tms}')",
            ),
            src_path=Depends(self.path_dependency),
            tile_format: ImageType = Query(
                ImageType.png, description="Output image type. Default is png."
            ),
            tile_scale: int = Query(
                1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
            ),
            minzoom: Optional[int] = Query(
                None, description="Overwrite default minzoom."
            ),
            maxzoom: Optional[int] = Query(
                None, description="Overwrite default maxzoom."
            ),
            layer_params=Depends(self.layer_dependency),  # noqa
            dataset_params=Depends(self.dataset_dependency),  # noqa
            buffer: Optional[float] = Query(  # noqa
                None,
                gt=0,
                title="Tile buffer.",
                description="Buffer on each side of the given tile. It must be a multiple of `0.5`. Output **tilesize** will be expanded to `tilesize + 2 * buffer` (e.g 0.5 = 257x257, 1.0 = 258x258).",
            ),
            post_process=Depends(self.process_dependency),  # noqa
            rescale: Optional[List[Tuple[float, ...]]] = Depends(
                RescalingParams
            ),  # noqa
            color_formula: Optional[str] = Query(  # noqa
                None,
                title="Color Formula",
                description="rio-color formula (info: https://github.com/mapbox/rio-color)",
            ),
            colormap=Depends(self.colormap_dependency),  # noqa
            render_params=Depends(self.render_dependency),  # noqa
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
                "TileMatrixSetId": TileMatrixSetId,
            }
            tiles_url = self.url_for(request, "tile", **route_params)

            qs_key_to_remove = [
                "tilematrixsetid",
                "tile_format",
                "tile_scale",
                "minzoom",
                "maxzoom",
                "service",
                "request",
            ]
            qs = [
                (key, value)
                for (key, value) in request.query_params._list
                if key.lower() not in qs_key_to_remove
            ]
            if qs:
                tiles_url += f"?{urlencode(qs)}"

            tms = self.supported_tms.get(TileMatrixSetId)
            with rasterio.Env(**env):
                with self.reader(src_path, tms=tms, **reader_params) as src_dst:
                    bounds = src_dst.geographic_bounds
                    minzoom = minzoom if minzoom is not None else src_dst.minzoom
                    maxzoom = maxzoom if maxzoom is not None else src_dst.maxzoom

            tileMatrix = []
            for zoom in range(minzoom, maxzoom + 1):
                matrix = tms.matrix(zoom)
                tm = f"""
                        <TileMatrix>
                            <ows:Identifier>{matrix.identifier}</ows:Identifier>
                            <ScaleDenominator>{matrix.scaleDenominator}</ScaleDenominator>
                            <TopLeftCorner>{matrix.topLeftCorner[0]} {matrix.topLeftCorner[1]}</TopLeftCorner>
                            <TileWidth>{matrix.tileWidth}</TileWidth>
                            <TileHeight>{matrix.tileHeight}</TileHeight>
                            <MatrixWidth>{matrix.matrixWidth}</MatrixWidth>
                            <MatrixHeight>{matrix.matrixHeight}</MatrixHeight>
                        </TileMatrix>"""
                tileMatrix.append(tm)

            return templates.TemplateResponse(
                "wmts.xml",
                {
                    "request": request,
                    "tiles_endpoint": tiles_url,
                    "bounds": bounds,
                    "tileMatrix": tileMatrix,
                    "tms": tms,
                    "title": "Cloud Optimized GeoTIFF",
                    "layer_name": "cogeo",
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
            lon: float = Path(..., description="Longitude"),
            lat: float = Path(..., description="Latitude"),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Point value for a dataset."""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params) as src_dst:
                    pts = src_dst.point(
                        lon,
                        lat,
                        **layer_params,
                        **dataset_params,
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
            format: ImageType = Query(
                None, description="Output image type. Default is auto."
            ),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            img_params=Depends(self.img_dependency),
            post_process=Depends(self.process_dependency),
            rescale: Optional[List[Tuple[float, ...]]] = Depends(RescalingParams),
            color_formula: Optional[str] = Query(
                None,
                title="Color Formula",
                description="rio-color formula (info: https://github.com/mapbox/rio-color)",
            ),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create preview of a dataset."""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params) as src_dst:
                    image = src_dst.preview(
                        **layer_params,
                        **img_params,
                        **dataset_params,
                    )
                    dst_colormap = getattr(src_dst, "colormap", None)

            if post_process:
                image = post_process(image)

            if rescale:
                image.rescale(rescale)

            if color_formula:
                image.apply_color_formula(color_formula)

            if not format:
                format = ImageType.jpeg if image.mask.all() else ImageType.png

            content = image.render(
                img_format=format.driver,
                colormap=colormap or dst_colormap,
                **format.profile,
                **render_params,
            )

            return Response(content, media_type=format.mediatype)

    ############################################################################
    # /crop (Optional)
    ############################################################################
    def part(self):
        """Register /crop endpoint."""

        # GET endpoints
        @self.router.get(
            r"/crop/{minx},{miny},{maxx},{maxy}.{format}",
            **img_endpoint_params,
        )
        @self.router.get(
            r"/crop/{minx},{miny},{maxx},{maxy}/{width}x{height}.{format}",
            **img_endpoint_params,
        )
        def part(
            minx: float = Path(..., description="Bounding box min X"),
            miny: float = Path(..., description="Bounding box min Y"),
            maxx: float = Path(..., description="Bounding box max X"),
            maxy: float = Path(..., description="Bounding box max Y"),
            format: ImageType = Query(..., description="Output image type."),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_dependency),
            post_process=Depends(self.process_dependency),
            rescale: Optional[List[Tuple[float, ...]]] = Depends(RescalingParams),
            color_formula: Optional[str] = Query(
                None,
                title="Color Formula",
                description="rio-color formula (info: https://github.com/mapbox/rio-color)",
            ),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create image from part of a dataset."""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params) as src_dst:
                    image = src_dst.part(
                        [minx, miny, maxx, maxy],
                        **layer_params,
                        **image_params,
                        **dataset_params,
                    )
                    dst_colormap = getattr(src_dst, "colormap", None)

            if post_process:
                image = post_process(image)

            if rescale:
                image.rescale(rescale)

            if color_formula:
                image.apply_color_formula(color_formula)

            content = image.render(
                img_format=format.driver,
                colormap=colormap or dst_colormap,
                **format.profile,
                **render_params,
            )

            return Response(content, media_type=format.mediatype)

        # POST endpoints
        @self.router.post(
            r"/crop",
            **img_endpoint_params,
        )
        @self.router.post(
            r"/crop.{format}",
            **img_endpoint_params,
        )
        @self.router.post(
            r"/crop/{width}x{height}.{format}",
            **img_endpoint_params,
        )
        def geojson_crop(
            geojson: Feature = Body(..., description="GeoJSON Feature."),
            format: ImageType = Query(
                None, description="Output image type. Default is auto."
            ),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_dependency),
            post_process=Depends(self.process_dependency),
            rescale: Optional[List[Tuple[float, ...]]] = Depends(RescalingParams),
            color_formula: Optional[str] = Query(
                None,
                title="Color Formula",
                description="rio-color formula (info: https://github.com/mapbox/rio-color)",
            ),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create image from a geojson feature."""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params) as src_dst:
                    image = src_dst.feature(
                        geojson.dict(exclude_none=True),
                        **layer_params,
                        **image_params,
                        **dataset_params,
                    )
                    dst_colormap = getattr(src_dst, "colormap", None)

            if post_process:
                image = post_process(image)

            if rescale:
                image.rescale(rescale)

            if color_formula:
                image.apply_color_formula(color_formula)

            if not format:
                format = ImageType.jpeg if image.mask.all() else ImageType.png

            content = image.render(
                img_format=format.driver,
                colormap=colormap or dst_colormap,
                **format.profile,
                **render_params,
            )

            return Response(content, media_type=format.mediatype)


@dataclass
class MultiBaseTilerFactory(TilerFactory):
    """Custom Tiler Factory for MultiBaseReader classes.

    Note:
        To be able to use the rio_tiler.io.MultiBaseReader we need to be able to pass a `assets`
        argument to most of its methods. By using the `AssetsBidxExprParams` for the `layer_dependency`, the
        .tile(), .point(), .preview() and the .part() methods will receive assets, expression or indexes arguments.

        The rio_tiler.io.MultiBaseReader  `.info()` and `.metadata()` have `assets` as
        a requirement arguments (https://github.com/cogeotiff/rio-tiler/blob/master/rio_tiler/io/base.py#L365).
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
                with self.reader(src_path, **reader_params) as src_dst:
                    return src_dst.info(**asset_params)

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
                with self.reader(src_path, **reader_params) as src_dst:
                    return Feature(
                        geometry=Polygon.from_bounds(*src_dst.geographic_bounds),
                        properties={
                            asset: asset_info
                            for asset, asset_info in src_dst.info(
                                **asset_params
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
                with self.reader(src_path, **reader_params) as src_dst:
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
            image_params=Depends(self.img_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Per Asset statistics"""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params) as src_dst:
                    return src_dst.statistics(
                        **asset_params,
                        **image_params,
                        **dataset_params,
                        **stats_params,
                        hist_options={**histogram_params},
                    )

        # MultiBaseReader merged statistics
        # https://github.com/cogeotiff/rio-tiler/blob/master/rio_tiler/io/base.py#L455-L468
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
            image_params=Depends(self.img_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Merged assets statistics."""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params) as src_dst:
                    # Default to all available assets
                    if not layer_params.assets and not layer_params.expression:
                        layer_params.assets = src_dst.assets

                    return src_dst.merged_statistics(
                        **layer_params,
                        **image_params,
                        **dataset_params,
                        **stats_params,
                        hist_options={**histogram_params},
                    )

        # POST endpoint
        @self.router.post(
            "/statistics",
            response_model=MultiBaseStatisticsGeoJSON,
            response_model_exclude_none=True,
            response_class=GeoJSONResponse,
            responses={
                200: {
                    "content": {"application/json": {}},
                    "description": "Return dataset's statistics.",
                }
            },
        )
        def geojson_statistics(
            geojson: Union[FeatureCollection, Feature] = Body(
                ..., description="GeoJSON Feature or FeatureCollection."
            ),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(AssetsBidxExprParamsOptional),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Statistics from a geojson feature or featureCollection."""
            fc = geojson
            if isinstance(fc, Feature):
                fc = FeatureCollection(features=[geojson])

            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params) as src_dst:
                    # Default to all available assets
                    if not layer_params.assets and not layer_params.expression:
                        layer_params.assets = src_dst.assets

                    for feature in fc:
                        data = src_dst.feature(
                            feature.dict(exclude_none=True),
                            **layer_params,
                            **image_params,
                            **dataset_params,
                        )

                        stats = get_array_statistics(
                            data.as_masked(),
                            **stats_params,
                            **histogram_params,
                        )

                    feature.properties = feature.properties or {}
                    feature.properties.update(
                        {
                            # NOTE: because we use `src_dst.feature` the statistics will be in form of
                            # `Dict[str, BandStatistics]` and not `Dict[str, Dict[str, BandStatistics]]`
                            "statistics": {
                                f"{data.band_names[ix]}": BandStatistics(**stats[ix])
                                for ix in range(len(stats))
                            }
                        }
                    )

            return fc.features[0] if isinstance(geojson, Feature) else fc


@dataclass
class MultiBandTilerFactory(TilerFactory):
    """Custom Tiler Factory for MultiBandReader classes.

    Note:
        To be able to use the rio_tiler.io.MultiBandReader we need to be able to pass a `bands`
        argument to most of its methods. By using the `BandsExprParams` for the `layer_dependency`, the
        .tile(), .point(), .preview() and the .part() methods will receive bands or expression arguments.

        The rio_tiler.io.MultiBandReader  `.info()` and `.metadata()` have `bands` as
        a requirement arguments (https://github.com/cogeotiff/rio-tiler/blob/master/rio_tiler/io/base.py#L775).
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
                with self.reader(src_path, **reader_params) as src_dst:
                    return src_dst.info(**bands_params)

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
                with self.reader(src_path, **reader_params) as src_dst:
                    return Feature(
                        geometry=Polygon.from_bounds(*src_dst.geographic_bounds),
                        properties=src_dst.info(**bands_params),
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
                with self.reader(src_path, **reader_params) as src_dst:
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
            image_params=Depends(self.img_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Dataset statistics."""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params) as src_dst:
                    return src_dst.statistics(
                        **bands_params,
                        **image_params,
                        **dataset_params,
                        **stats_params,
                        hist_options={**histogram_params},
                    )

        # POST endpoint
        @self.router.post(
            "/statistics",
            response_model=StatisticsGeoJSON,
            response_model_exclude_none=True,
            response_class=GeoJSONResponse,
            responses={
                200: {
                    "content": {"application/json": {}},
                    "description": "Return dataset's statistics.",
                }
            },
        )
        def geojson_statistics(
            geojson: Union[FeatureCollection, Feature] = Body(
                ..., description="GeoJSON Feature or FeatureCollection."
            ),
            src_path=Depends(self.path_dependency),
            bands_params=Depends(BandsExprParamsOptional),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Statistics from a geojson feature or featureCollection."""
            fc = geojson
            if isinstance(fc, Feature):
                fc = FeatureCollection(features=[geojson])

            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params) as src_dst:
                    # Default to all available bands
                    if not bands_params.bands and not bands_params.expression:
                        bands_params.bands = src_dst.bands

                    for feature in fc:
                        data = src_dst.feature(
                            feature.dict(exclude_none=True),
                            **bands_params,
                            **image_params,
                            **dataset_params,
                        )
                        stats = get_array_statistics(
                            data.as_masked(),
                            **stats_params,
                            **histogram_params,
                        )

                        feature.properties = feature.properties or {}
                        feature.properties.update(
                            {
                                "statistics": {
                                    f"{data.band_names[ix]}": BandStatistics(
                                        **stats[ix]
                                    )
                                    for ix in range(len(stats))
                                }
                            }
                        )

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
            base_url += self.router_prefix.lstrip("/")
        return url_path.make_absolute_url(base_url=base_url)

    def register_routes(self):
        """Register TMS endpoint routes."""

        @self.router.get(
            r"/tileMatrixSets",
            response_model=TileMatrixSetList,
            response_model_exclude_none=True,
            summary="Retrieve the list of available tiling schemes (tile matrix sets).",
            operation_id="getTileMatrixSetsList",
        )
        async def TileMatrixSet_list(request: Request):
            """
            OGC Specification: http://docs.opengeospatial.org/per/19-069.html#_tilematrixsets
            """
            return {
                "tileMatrixSets": [
                    {
                        "id": tms.identifier,
                        "title": tms.identifier,
                        "links": [
                            {
                                "href": self.url_for(
                                    request,
                                    "TileMatrixSet_info",
                                    TileMatrixSetId=tms.identifier,
                                ),
                                "rel": "item",
                                "type": "application/json",
                            }
                        ],
                    }
                    for tms in self.supported_tms.tms.values()
                ]
            }

        @self.router.get(
            r"/tileMatrixSets/{TileMatrixSetId}",
            response_model=TileMatrixSet,
            response_model_exclude_none=True,
            summary="Retrieve the definition of the specified tiling scheme (tile matrix set).",
            operation_id="getTileMatrixSet",
        )
        async def TileMatrixSet_info(
            TileMatrixSetId: Literal[tuple(self.supported_tms.list())] = Path(
                ..., description="TileMatrixSet Name."
            )
        ):
            """
            OGC Specification: http://docs.opengeospatial.org/per/19-069.html#_tilematrixset
            """
            return self.supported_tms.get(TileMatrixSetId)


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
            props = algorithm.schema()["properties"]

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
                if not k.startswith("input_") and not k.startswith("output_")
            }
            return AlgorithmMetadata(inputs=ins, outputs=outs, parameters=params)

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
            algorithm: Literal[tuple(self.supported_algorithm.list())] = Path(
                ..., description="Algorithm name", alias="algorithmId"
            ),
        ):
            """Retrieve the metadata of the specified algorithm."""
            return metadata(self.supported_algorithm.get(algorithm))
