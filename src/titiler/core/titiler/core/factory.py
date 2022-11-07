"""TiTiler Router factories."""

import abc
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union
from urllib.parse import urlencode

from geojson_pydantic.features import Feature, FeatureCollection
from morecantile import TileMatrixSet
from rio_tiler.io import BaseReader, COGReader, MultiBandReader, MultiBaseReader
from rio_tiler.models import Bounds, Info
from rio_tiler.types import ColorMapType

import titiler.core.gis_tools as gt
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
    PostProcessParams,
    StatisticsParams,
    TileMatrixSetName,
    TMSParams,
)
from titiler.core.models.mapbox import TileJSON
from titiler.core.models.OGC import TileMatrixSetList
from titiler.core.models.responses import (
    InfoGeoJSON,
    MultiBaseInfo,
    MultiBaseInfoGeoJSON,
    MultiBasePoint,
    MultiBaseStatistics,
    MultiBaseStatisticsGeoJSON,
    Point,
    Statistics,
    StatisticsGeoJSON,
)
from titiler.core.resources.enums import ImageType, OptionalHeader
from titiler.core.resources.responses import GeoJSONResponse, JSONResponse, XMLResponse
from titiler.core.routing import EndpointScope
from titiler.core.utils import Timer

from fastapi import APIRouter, Body, Depends, Path, Query, params
from fastapi.dependencies.utils import get_parameterless_sub_dependant

from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match

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
        reader (rio_tiler.io.base.BaseReader): A rio-tiler reader (e.g COGReader).
        router (fastapi.APIRouter): Application router to register endpoints to.
        path_dependency (Callable): Endpoint dependency defining `path` to pass to the reader init.
        dataset_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining dataset overwriting options (e.g nodata).
        layer_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining dataset indexes/bands/assets options.
        render_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining image rendering options (e.g add_mask).
        colormap_dependency (Callable): Endpoint dependency defining ColorMap options (e.g colormap_name).
        stats_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining options for rio-tiler's statistics method.
        histogram_dependency (titiler.core.dependencies.DefaultDependency): Endpoint dependency defining options for numpy's histogram method.
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

    # Statistics/Histogram Dependencies
    stats_dependency: Type[DefaultDependency] = StatisticsParams
    histogram_dependency: Type[DefaultDependency] = HistogramParams

    # Post Processing Dependencies (rescaling, color-formula)
    process_dependency: Type[DefaultDependency] = PostProcessParams

    # TileMatrixSet dependency
    tms_dependency: Callable[..., TileMatrixSet] = TMSParams

    # Reader dependency
    reader_dependency: Type[DefaultDependency] = DefaultDependency

    # GDAL ENV dependency
    environment_dependency: Callable[..., Dict] = lambda: dict()

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
    """Tiler Factory."""

    # Default reader is set to COGReader
    reader: Type[BaseReader] = COGReader

    # Crop/Preview endpoints Dependencies
    img_dependency: Type[DefaultDependency] = ImageParams

    # Add/Remove some endpoints
    add_preview: bool = True
    add_part: bool = True

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
            return gt.bounds(
                reader=self.reader,
                env=env,
                src_path=src_path,
                reader_params=reader_params,
            )

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
            return gt.info(
                reader=self.reader,
                env=env,
                src_path=src_path,
                reader_params=reader_params,
            )

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
            return gt.info_geojson(
                reader=self.reader,
                env=env,
                src_path=src_path,
                reader_params=reader_params,
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
            return gt.statistics(
                reader=self.reader,
                env=env,
                src_path=src_path,
                reader_params=reader_params,
                stat_params={
                    **layer_params,
                    **image_params,
                    **dataset_params,
                    **stats_params,
                },
                histogram_params=histogram_params,
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
            return gt.geojson_statistics(
                geojson=geojson,
                reader=self.reader,
                env=env,
                src_path=src_path,
                reader_params=reader_params,
                feature_params={**layer_params, **image_params, **dataset_params},
                stats_params={**stats_params, **histogram_params},
            )

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
            tms: TileMatrixSet = Depends(self.tms_dependency),
            scale: int = Query(
                1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
            ),
            format: ImageType = Query(
                None, description="Output image type. Default is auto."
            ),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            postprocess_params=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            tile_buffer: Optional[float] = Query(
                None,
                gt=0,
                alias="buffer",
                title="Tile buffer.",
                description="Buffer on each side of the given tile. It must be a multiple of `0.5`. Output **tilesize** will be expanded to `tilesize + 2 * tile_buffer` (e.g 0.5 = 257x257, 1.0 = 258x258).",
            ),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create map tile from a dataset."""
            headers: Dict[str, str] = {}

            content, timings = gt.tile(
                reader=self.reader,
                env=env,
                src_path=src_path,
                reader_params=reader_params,
                z=z,
                x=x,
                y=y,
                tms=tms,
                scale=scale,
                format=format,
                tile_params={**layer_params, **dataset_params},
                postprocess_params=postprocess_params,
                colormap=colormap,
                render_params=render_params,
                tile_buffer=tile_buffer,
            )

            if OptionalHeader.server_timing in self.optional_headers:
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            return Response(content, media_type=format.mediatype, headers=headers)

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
            tms: TileMatrixSet = Depends(self.tms_dependency),
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
            postprocess_params=Depends(self.process_dependency),  # noqa
            colormap=Depends(self.colormap_dependency),  # noqa
            render_params=Depends(self.render_dependency),  # noqa
            tile_buffer: Optional[float] = Query(  # noqa
                None,
                gt=0,
                alias="buffer",
                title="Tile buffer.",
                description="Buffer on each side of the given tile. It must be a multiple of `0.5`. Output **tilesize** will be expanded to `tilesize + 2 * tile_buffer` (e.g 0.5 = 257x257, 1.0 = 258x258).",
            ),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return TileJSON document for a dataset."""
            route_params = {
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
                "scale": tile_scale,
                "TileMatrixSetId": tms.identifier,
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

            reader_params["tms"] = tms
            return gt.tilejson(
                reader=self.reader,
                env=env,
                src_path=src_path,
                reader_params=reader_params,
                tiles_url=tiles_url,
                minzoom=minzoom,
                maxzoom=maxzoom,
            )

    def wmts(self):  # noqa: C901
        """Register /wmts endpoint."""

        @self.router.get("/WMTSCapabilities.xml", response_class=XMLResponse)
        @self.router.get(
            "/{TileMatrixSetId}/WMTSCapabilities.xml", response_class=XMLResponse
        )
        def wmts(
            request: Request,
            tms: TileMatrixSet = Depends(self.tms_dependency),
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
            postprocess_params=Depends(self.process_dependency),  # noqa
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
                "TileMatrixSetId": tms.identifier,
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

            return gt.wmts(
                reader=self.reader,
                env=env,
                src_path=src_path,
                reader_params=reader_params,
                request=request,
                tile_format=tile_format,
                tms=tms,
                tiles_url=tiles_url,
                minzoom=minzoom,
                maxzoom=maxzoom,
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
            response: Response,
            lon: float = Path(..., description="Longitude"),
            lat: float = Path(..., description="Latitude"),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Point value for a dataset."""
            timings = []
            with Timer() as t:
                result = gt.point(
                    reader=self.reader,
                    env=env,
                    src_path=src_path,
                    reader_params=reader_params,
                    lon=lon,
                    lat=lat,
                    layer_params=layer_params,
                    dataset_params=dataset_params,
                )
            timings.append(("dataread", round(t.elapsed * 1000, 2)))

            if OptionalHeader.server_timing in self.optional_headers:
                response.headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            return result

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
            postprocess_params=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create preview of a dataset."""
            headers: Dict[str, str] = {}

            timings, content = gt.preview(
                reader=self.reader,
                format=format,
                src_path=src_path,
                preview_params={
                    **layer_params,
                    **img_params,
                    **dataset_params,
                },
                postprocess_params=postprocess_params,
                colormap=colormap,
                render_params=render_params,
                reader_params=reader_params,
                env=env,
            )

            if OptionalHeader.server_timing in self.optional_headers:
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            return Response(content, media_type=format.mediatype, headers=headers)

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
            postprocess_params=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create image from part of a dataset."""
            headers: Dict[str, str] = {}

            timings, content = gt.part(
                minx=minx,
                miny=miny,
                maxx=maxx,
                maxy=maxy,
                reader=self.reader,
                format=format,
                src_path=src_path,
                part_params={
                    **layer_params,
                    **image_params,
                    **dataset_params,
                },
                postprocess_params=postprocess_params,
                colormap=colormap,
                render_params=render_params,
                reader_params=reader_params,
                env=env,
            )

            if OptionalHeader.server_timing in self.optional_headers:
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            return Response(content, media_type=format.mediatype, headers=headers)

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
            postprocess_params=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create image from a geojson feature."""
            headers: Dict[str, str] = {}

            timings, content = gt.geojson_crop(
                geojson=geojson,
                reader=self.reader,
                reader_params=reader_params,
                format=format,
                src_path=src_path,
                part_params={
                    **layer_params,
                    **dataset_params,
                    **image_params,
                },
                postprocess_params=postprocess_params,
                colormap=colormap,
                render_params=render_params,
                env=env,
            )

            if OptionalHeader.server_timing in self.optional_headers:
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            return Response(content, media_type=format.mediatype, headers=headers)


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

    ############################################################################
    # /point
    ############################################################################
    def point(self):
        """Register /point endpoints."""

        @self.router.get(
            r"/point/{lon},{lat}",
            response_model=MultiBasePoint,
            response_class=JSONResponse,
            responses={200: {"description": "Return a value for a point"}},
        )
        def point(
            response: Response,
            lon: float = Path(..., description="Longitude"),
            lat: float = Path(..., description="Latitude"),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Point value for a dataset."""
            timings = []
            with Timer() as t:
                result = gt.point(
                    reader=self.reader,
                    env=env,
                    src_path=src_path,
                    reader_params=reader_params,
                    lon=lon,
                    lat=lat,
                    layer_params=layer_params,
                    dataset_params=dataset_params,
                )
            timings.append(("dataread", round(t.elapsed * 1000, 2)))

            if OptionalHeader.server_timing in self.optional_headers:
                response.headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            return result

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
            return gt.info(
                reader=self.reader,
                env=env,
                src_path=src_path,
                reader_params=reader_params,
                info_params=asset_params,
            )

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
            return gt.info_geojson_multi(
                reader=self.reader,
                env=env,
                src_path=src_path,
                reader_params=reader_params,
                asset_params=asset_params,
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
            return gt.assets(
                reader=self.reader,
                env=env,
                src_path=src_path,
                reader_params=reader_params,
            )

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
            return gt.statistics(
                reader=self.reader,
                env=env,
                src_path=src_path,
                reader_params=reader_params,
                stat_params={
                    **asset_params,
                    **image_params,
                    **dataset_params,
                    **stats_params,
                },
                histogram_params=histogram_params,
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
            return gt.statistics(
                reader=self.reader,
                reader_params=reader_params,
                env=env,
                src_path=src_path,
                stats_params={
                    **stats_params,
                    **layer_params,
                    **dataset_params,
                    **image_params,
                },
                histogram_params=histogram_params,
                multi_assets=True,
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
            return gt.geojson_statistics(
                reader=self.reader,
                env=env,
                src_path=src_path,
                reader_params=reader_params,
                geojson=geojson,
                multi_assets=True,
                feature_params={
                    **layer_params,
                    **image_params,
                    **dataset_params,
                },
                stats_params={**stats_params, **histogram_params},
            )


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
            return gt.info(
                reader=self.reader,
                env=env,
                src_path=src_path,
                reader_params=reader_params,
                info_params=bands_params,
            )

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
            return gt.info_geojson(
                reader=self.reader,
                env=env,
                src_path=src_path,
                reader_params=reader_params,
                info_params=bands_params,
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
            return gt.bands(
                reader=self.reader,
                env=env,
                src_path=src_path,
                reader_params=reader_params,
            )

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
            """Create image from a geojson feature."""
            return gt.statistics(
                reader=self.reader,
                env=env,
                src_path=src_path,
                reader_params=reader_params,
                stat_params={
                    **bands_params,
                    **image_params,
                    **dataset_params,
                    **stats_params,
                },
                histogram_params=histogram_params,
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

            return gt.geojson_statistics(
                geojson=geojson,
                reader=self.reader,
                env=env,
                src_path=src_path,
                reader_params=reader_params,
                feature_params={**bands_params, **image_params, **dataset_params},
                stats_params={
                    **stats_params,
                    **histogram_params,
                },
            )


@dataclass
class TMSFactory:
    """TileMatrixSet endpoints Factory."""

    # Enum of supported TMS
    supported_tms: Type[TileMatrixSetName] = TileMatrixSetName

    # TileMatrixSet dependency
    tms_dependency: Callable[..., TileMatrixSet] = TMSParams

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
        )
        async def TileMatrixSet_list(request: Request):
            """
            Return list of supported TileMatrixSets.

            Specs: http://docs.opengeospatial.org/per/19-069.html#_tilematrixsets
            """
            return {
                "tileMatrixSets": [
                    {
                        "id": tms.name,
                        "title": tms.name,
                        "links": [
                            {
                                "href": self.url_for(
                                    request,
                                    "TileMatrixSet_info",
                                    TileMatrixSetId=tms.name,
                                ),
                                "rel": "item",
                                "type": "application/json",
                            }
                        ],
                    }
                    for tms in self.supported_tms
                ]
            }

        @self.router.get(
            r"/tileMatrixSets/{TileMatrixSetId}",
            response_model=TileMatrixSet,
            response_model_exclude_none=True,
        )
        async def TileMatrixSet_info(tms: TileMatrixSet = Depends(self.tms_dependency)):
            """Return TileMatrixSet JSON document."""
            return tms
