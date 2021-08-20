"""TiTiler Router factories."""

import abc
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, Union
from urllib.parse import urlencode, urlparse

import rasterio
from geojson_pydantic.features import Feature, FeatureCollection
from morecantile import TileMatrixSet
from rio_tiler.io import BaseReader, COGReader, MultiBandReader, MultiBaseReader
from rio_tiler.models import Bounds, Info, Metadata

from titiler.core.dependencies import (
    AssetsBidxExprParams,
    AssetsBidxParams,
    BandsExprParams,
    BandsParams,
    BidxExprParams,
    BidxParams,
    ColorMapParams,
    DatasetParams,
    DatasetPathParams,
    DefaultDependency,
    ImageParams,
    MetadataParams,
    RenderParams,
    TileMatrixSetName,
    TMSParams,
    WebMercatorTMSParams,
)
from titiler.core.models.mapbox import TileJSON
from titiler.core.models.OGC import TileMatrixSetList
from titiler.core.resources.enums import ImageType, MediaType, OptionalHeader
from titiler.core.resources.responses import GeoJSONResponse, XMLResponse
from titiler.core.utils import Timer, bbox_to_feature, data_stats

from fastapi import APIRouter, Body, Depends, Path, Query

from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore

templates = Jinja2Templates(directory=str(resources_files(__package__) / "templates"))


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
    """BaseTiler Factory."""

    reader: Type[BaseReader]
    reader_options: Dict = field(default_factory=dict)

    # FastAPI router
    router: APIRouter = field(default_factory=APIRouter)

    # Path Dependency
    path_dependency: Callable[..., str] = DatasetPathParams

    # Rasterio Dataset Options (nodata, unscale, resampling)
    dataset_dependency: Type[DefaultDependency] = DatasetParams

    # Indexes/Expression Dependencies
    layer_dependency: Type[DefaultDependency] = BidxExprParams

    # Image rendering Dependencies
    render_dependency: Type[DefaultDependency] = RenderParams

    colormap_dependency: Callable[..., Optional[Dict]] = ColorMapParams

    # TileMatrixSet dependency
    tms_dependency: Callable[..., TileMatrixSet] = WebMercatorTMSParams

    # provide custom dependency
    additional_dependency: Callable[..., Dict] = lambda: dict()

    # Router Prefix is needed to find the path for /tile if the TilerFactory.router is mounted
    # with other router (multiple `.../tile` routes).
    # e.g if you mount the route with `/cog` prefix, set router_prefix to cog and
    router_prefix: str = ""

    # Add specific GDAL environement (e.g {"AWS_REQUEST_PAYER": "requester"})
    gdal_config: Dict = field(default_factory=dict)

    # add additional headers in response
    optional_headers: List[OptionalHeader] = field(default_factory=list)

    def __post_init__(self):
        """Post Init: register route and configure specific options."""
        self.register_routes()

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


@dataclass
class TilerFactory(BaseTilerFactory):
    """Tiler Factory."""

    # Default reader is set to COGReader
    reader: Type[BaseReader] = COGReader

    # Endpoint Dependencies
    metadata_dependency: Type[DefaultDependency] = MetadataParams
    img_dependency: Type[DefaultDependency] = ImageParams

    # TileMatrixSet dependency
    tms_dependency: Callable[..., TileMatrixSet] = TMSParams

    # Add/Remove some endpoints
    add_preview: bool = True
    add_part: bool = True
    add_statistics: bool = True

    def register_routes(self):
        """
        This Method register routes to the router.

        Because we wrap the endpoints in a class we cannot define the routes as
        methods (because of the self argument). The HACK is to define routes inside
        the class method and register them after the class initialisation.

        """
        # Default Routes
        # (/bounds, /info, /metadata, /tile, /tilejson.json, /WMTSCapabilities.xml and /point)
        self.bounds()
        self.info()
        self.metadata()
        self.tile()
        self.tilejson()
        self.wmts()
        self.point()

        if self.add_preview:
            self.preview()

        if self.add_part:
            self.part()

        if self.add_statistics:
            self.statistics()

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
        def bounds(src_path=Depends(self.path_dependency)):
            """Return the bounds of the COG."""
            with rasterio.Env(**self.gdal_config):
                with self.reader(src_path, **self.reader_options) as src_dst:
                    return {"bounds": src_dst.bounds}

    ############################################################################
    # /info
    ############################################################################
    def info(self):
        """Register /info endpoint."""

        @self.router.get(
            "/info",
            response_model=Info,
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={200: {"description": "Return dataset's basic info."}},
        )
        def info(
            src_path=Depends(self.path_dependency),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Return dataset's basic info."""
            with rasterio.Env(**self.gdal_config):
                with self.reader(src_path, **self.reader_options) as src_dst:
                    return src_dst.info(**kwargs)

        @self.router.get(
            "/info.geojson",
            response_model=Feature,
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
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Return dataset's basic info as a GeoJSON feature."""
            with rasterio.Env(**self.gdal_config):
                with self.reader(src_path, **self.reader_options) as src_dst:
                    info = src_dst.info(**kwargs).dict(exclude_none=True)
                    bounds = info.pop("bounds", None)
                    info.pop("center", None)
                    info.pop("minzoom", None)
                    info.pop("maxzoom", None)
                    info["dataset"] = src_path
                    geojson = bbox_to_feature(bounds, properties=info)

            return geojson

    ############################################################################
    # /metadata
    ############################################################################
    def metadata(self):
        """Register /metadata endpoint"""

        @self.router.get(
            "/metadata",
            response_model=Metadata,
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={200: {"description": "Return dataset's metadata."}},
        )
        def metadata(
            src_path=Depends(self.path_dependency),
            metadata_params=Depends(self.metadata_dependency),
            layer_params=Depends(BidxParams),
            dataset_params=Depends(self.dataset_dependency),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Return metadata."""
            with rasterio.Env(**self.gdal_config):
                with self.reader(src_path, **self.reader_options) as src_dst:
                    return src_dst.metadata(
                        metadata_params.pmin,
                        metadata_params.pmax,
                        **layer_params.kwargs,
                        **metadata_params.kwargs,
                        **dataset_params.kwargs,
                        **kwargs,
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
            z: int = Path(..., ge=0, le=30, description="Mercator tiles's zoom level"),
            x: int = Path(..., description="Mercator tiles's column"),
            y: int = Path(..., description="Mercator tiles's row"),
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
            render_params=Depends(self.render_dependency),
            colormap=Depends(self.colormap_dependency),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Create map tile from a dataset."""
            timings = []
            headers: Dict[str, str] = {}

            tilesize = scale * 256

            with Timer() as t:
                with rasterio.Env(**self.gdal_config):
                    with self.reader(
                        src_path, tms=tms, **self.reader_options
                    ) as src_dst:
                        data = src_dst.tile(
                            x,
                            y,
                            z,
                            tilesize=tilesize,
                            **layer_params.kwargs,
                            **dataset_params.kwargs,
                            **kwargs,
                        )
                        dst_colormap = getattr(src_dst, "colormap", None)
            timings.append(("dataread", round(t.elapsed * 1000, 2)))

            if not format:
                format = ImageType.jpeg if data.mask.all() else ImageType.png

            with Timer() as t:
                image = data.post_process(
                    in_range=render_params.rescale_range,
                    color_formula=render_params.color_formula,
                )
            timings.append(("postprocess", round(t.elapsed * 1000, 2)))

            with Timer() as t:
                content = image.render(
                    add_mask=render_params.return_mask,
                    img_format=format.driver,
                    colormap=colormap or dst_colormap,
                    **format.profile,
                    **render_params.kwargs,
                )
            timings.append(("format", round(t.elapsed * 1000, 2)))

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
            render_params=Depends(self.render_dependency),  # noqa
            colormap=Depends(self.colormap_dependency),  # noqa
            kwargs: Dict = Depends(self.additional_dependency),  # noqa
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

            with rasterio.Env(**self.gdal_config):
                with self.reader(src_path, tms=tms, **self.reader_options) as src_dst:
                    center = list(src_dst.center)
                    if minzoom:
                        center[-1] = minzoom
                    tjson = {
                        "bounds": src_dst.bounds,
                        "center": tuple(center),
                        "minzoom": minzoom if minzoom is not None else src_dst.minzoom,
                        "maxzoom": maxzoom if maxzoom is not None else src_dst.maxzoom,
                        "name": urlparse(src_path).path.lstrip("/") or "cogeotif",
                        "tiles": [tiles_url],
                    }

            return tjson

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
            render_params=Depends(self.render_dependency),  # noqa
            colormap=Depends(self.colormap_dependency),  # noqa
            kwargs: Dict = Depends(self.additional_dependency),  # noqa
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

            with rasterio.Env(**self.gdal_config):
                with self.reader(src_path, tms=tms, **self.reader_options) as src_dst:
                    bounds = src_dst.bounds
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
            responses={200: {"description": "Return a value for a point"}},
        )
        def point(
            response: Response,
            lon: float = Path(..., description="Longitude"),
            lat: float = Path(..., description="Latitude"),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Get Point value for a dataset."""
            timings = []

            with Timer() as t:
                with rasterio.Env(**self.gdal_config):
                    with self.reader(src_path, **self.reader_options) as src_dst:
                        values = src_dst.point(
                            lon,
                            lat,
                            **layer_params.kwargs,
                            **dataset_params.kwargs,
                            **kwargs,
                        )
            timings.append(("dataread", round(t.elapsed * 1000, 2)))

            if OptionalHeader.server_timing in self.optional_headers:
                response.headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            return {"coordinates": [lon, lat], "values": values}

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
            img_params=Depends(self.img_dependency),
            dataset_params=Depends(self.dataset_dependency),
            render_params=Depends(self.render_dependency),
            colormap=Depends(self.colormap_dependency),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Create preview of a dataset."""
            timings = []
            headers: Dict[str, str] = {}

            with Timer() as t:
                with rasterio.Env(**self.gdal_config):
                    with self.reader(src_path, **self.reader_options) as src_dst:
                        data = src_dst.preview(
                            **layer_params.kwargs,
                            **img_params.kwargs,
                            **dataset_params.kwargs,
                            **kwargs,
                        )
                        dst_colormap = getattr(src_dst, "colormap", None)
            timings.append(("dataread", round(t.elapsed * 1000, 2)))

            if not format:
                format = ImageType.jpeg if data.mask.all() else ImageType.png

            with Timer() as t:
                image = data.post_process(
                    in_range=render_params.rescale_range,
                    color_formula=render_params.color_formula,
                )
            timings.append(("postprocess", round(t.elapsed * 1000, 2)))

            with Timer() as t:
                content = image.render(
                    add_mask=render_params.return_mask,
                    img_format=format.driver,
                    colormap=colormap or dst_colormap,
                    **format.profile,
                    **render_params.kwargs,
                )
            timings.append(("format", round(t.elapsed * 1000, 2)))

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

        @self.router.get(
            r"/crop/{minx},{miny},{maxx},{maxy}.{format}", **img_endpoint_params,
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
            image_params=Depends(self.img_dependency),
            dataset_params=Depends(self.dataset_dependency),
            render_params=Depends(self.render_dependency),
            colormap=Depends(self.colormap_dependency),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Create image from part of a dataset."""
            timings = []
            headers: Dict[str, str] = {}

            with Timer() as t:
                with rasterio.Env(**self.gdal_config):
                    with self.reader(src_path, **self.reader_options) as src_dst:
                        data = src_dst.part(
                            [minx, miny, maxx, maxy],
                            **layer_params.kwargs,
                            **image_params.kwargs,
                            **dataset_params.kwargs,
                            **kwargs,
                        )
                        dst_colormap = getattr(src_dst, "colormap", None)
            timings.append(("dataread", round(t.elapsed * 1000, 2)))

            with Timer() as t:
                image = data.post_process(
                    in_range=render_params.rescale_range,
                    color_formula=render_params.color_formula,
                )
            timings.append(("postprocess", round(t.elapsed * 1000, 2)))

            with Timer() as t:
                content = image.render(
                    add_mask=render_params.return_mask,
                    img_format=format.driver,
                    colormap=colormap or dst_colormap,
                    **format.profile,
                    **render_params.kwargs,
                )
            timings.append(("format", round(t.elapsed * 1000, 2)))

            if OptionalHeader.server_timing in self.optional_headers:
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            return Response(content, media_type=format.mediatype, headers=headers)

        @self.router.post(
            r"/crop", **img_endpoint_params,
        )
        @self.router.post(
            r"/crop.{format}", **img_endpoint_params,
        )
        @self.router.post(
            r"/crop/{width}x{height}.{format}", **img_endpoint_params,
        )
        def geojson_crop(
            feature: Feature = Body(..., descriptiom="GeoJSON Feature."),
            format: ImageType = Query(
                None, description="Output image type. Default is auto."
            ),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            image_params=Depends(self.img_dependency),
            dataset_params=Depends(self.dataset_dependency),
            render_params=Depends(self.render_dependency),
            colormap=Depends(self.colormap_dependency),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Create image from a geojson feature."""
            timings = []
            headers: Dict[str, str] = {}

            with Timer() as t:
                with rasterio.Env(**self.gdal_config):
                    with self.reader(src_path, **self.reader_options) as src_dst:
                        data = src_dst.feature(
                            feature.dict(exclude_none=True),
                            **layer_params.kwargs,
                            **image_params.kwargs,
                            **dataset_params.kwargs,
                            **kwargs,
                        )
                        dst_colormap = getattr(src_dst, "colormap", None)
            timings.append(("dataread", round(t.elapsed * 1000, 2)))

            with Timer() as t:
                image = data.post_process(
                    in_range=render_params.rescale_range,
                    color_formula=render_params.color_formula,
                )
            timings.append(("postprocess", round(t.elapsed * 1000, 2)))

            if not format:
                format = ImageType.jpeg if data.mask.all() else ImageType.png

            with Timer() as t:
                content = image.render(
                    add_mask=render_params.return_mask,
                    img_format=format.driver,
                    colormap=colormap or dst_colormap,
                    **format.profile,
                    **render_params.kwargs,
                )
            timings.append(("format", round(t.elapsed * 1000, 2)))

            if OptionalHeader.server_timing in self.optional_headers:
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            return Response(content, media_type=format.mediatype, headers=headers)

    ############################################################################
    # /statistics (Optional)
    ############################################################################
    def statistics(self):
        """add statistics endpoints."""

        @self.router.get(
            "/statistics",
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
            image_params=Depends(self.img_dependency),
            dataset_params=Depends(self.dataset_dependency),
            categorical: bool = Query(
                False, description="Return statistics for categorical dataset."
            ),
            c: List[Union[float, int]] = Query(
                None, description="Pixels values for categories."
            ),
            p: List[int] = Query([2, 98], description="Percentile values."),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Create image from a geojson feature."""
            with rasterio.Env(**self.gdal_config):
                with self.reader(src_path, **self.reader_options) as src_dst:
                    data = src_dst.preview(
                        **layer_params.kwargs,
                        **image_params.kwargs,
                        **dataset_params.kwargs,
                        **kwargs,
                    ).as_masked()

            return data_stats(
                data, categorical=categorical, categories=c, percentiles=p
            )

        @self.router.post(
            "/statistics",
            response_model=Union[Feature, FeatureCollection],
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
            features: Union[FeatureCollection, Feature] = Body(
                ..., descriptiom="GeoJSON Feature or FeatureCollection."
            ),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            image_params=Depends(self.img_dependency),
            dataset_params=Depends(self.dataset_dependency),
            categorical: bool = Query(
                False, description="Return statistics for categorical dataset."
            ),
            c: List[Union[float, int]] = Query(
                None, description="Pixels values for categories."
            ),
            p: List[int] = Query([2, 98], description="Percentile values."),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Create image from a geojson feature."""
            if isinstance(features, FeatureCollection):
                feat = []
                for feature in features:
                    with rasterio.Env(**self.gdal_config):
                        with self.reader(src_path, **self.reader_options) as src_dst:
                            data = src_dst.feature(
                                feature.dict(exclude_none=True),
                                **layer_params.kwargs,
                                **image_params.kwargs,
                                **dataset_params.kwargs,
                                **kwargs,
                            ).as_masked()

                        feature.properties.update(
                            {
                                "statistics": data_stats(
                                    data,
                                    categorical=categorical,
                                    categories=c,
                                    percentiles=p,
                                )
                            }
                        )
                        feat.append(feature)
                return FeatureCollection(features=feat)
            else:
                with rasterio.Env(**self.gdal_config):
                    with self.reader(src_path, **self.reader_options) as src_dst:
                        data = src_dst.feature(
                            features.dict(exclude_none=True),
                            **layer_params.kwargs,
                            **image_params.kwargs,
                            **dataset_params.kwargs,
                            **kwargs,
                        ).as_masked()

                features.properties.update(
                    {
                        "statistics": data_stats(
                            data, categorical=categorical, categories=c, percentiles=p,
                        )
                    }
                )
                return features


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

    # Assets/Indexes/Expression Dependencies
    layer_dependency: Type[DefaultDependency] = AssetsBidxExprParams

    # Overwrite the `/info` endpoint to return the list of assets when no assets is passed.
    def info(self):
        """Register /info endpoint."""

        @self.router.get(
            "/info",
            response_model=Dict[str, Info],
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={
                200: {
                    "description": "Return dataset's basic info or the list of available assets."
                }
            },
        )
        def info(
            src_path=Depends(self.path_dependency),
            asset_params=Depends(AssetsBidxParams),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Return dataset's basic info or the list of available assets."""
            with rasterio.Env(**self.gdal_config):
                with self.reader(src_path, **self.reader_options) as src_dst:
                    return src_dst.info(**asset_params.kwargs, **kwargs)

        @self.router.get(
            "/info.geojson",
            response_model=Feature,
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
            asset_params=Depends(AssetsBidxParams),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Return dataset's basic info as a GeoJSON feature."""
            with rasterio.Env(**self.gdal_config):
                with self.reader(src_path, **self.reader_options) as src_dst:
                    info = {"dataset": src_path}
                    info["assets"] = {
                        asset: meta.dict(exclude_none=True)
                        for asset, meta in src_dst.info(
                            **asset_params.kwargs, **kwargs
                        ).items()
                    }
                    geojson = bbox_to_feature(src_dst.bounds, properties=info)

            return geojson

        @self.router.get(
            "/assets",
            response_model=List[str],
            responses={200: {"description": "Return a list of supported assets."}},
        )
        def available_assets(
            src_path=Depends(self.path_dependency),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Return a list of supported assets."""
            with rasterio.Env(**self.gdal_config):
                with self.reader(src_path, **self.reader_options) as src_dst:
                    return src_dst.assets

    # Overwrite the `/metadata` endpoint because the MultiBaseReader output model is different (Dict[str, cogMetadata])
    # and MultiBaseReader.metadata() method also has `assets` as a requirement arguments.
    def metadata(self):
        """Register /metadata endpoint."""

        @self.router.get(
            "/metadata",
            response_model=Dict[str, Metadata],
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={200: {"description": "Return dataset's metadata."}},
        )
        def metadata(
            src_path=Depends(self.path_dependency),
            asset_params=Depends(AssetsBidxParams),
            metadata_params=Depends(self.metadata_dependency),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Return metadata."""
            with rasterio.Env(**self.gdal_config):
                with self.reader(src_path, **self.reader_options) as src_dst:
                    return src_dst.metadata(
                        metadata_params.pmin,
                        metadata_params.pmax,
                        **asset_params.kwargs,
                        **metadata_params.kwargs,
                        **kwargs,
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

    # Assets/Expression Dependencies
    layer_dependency: Type[DefaultDependency] = BandsExprParams

    def info(self):
        """Register /info endpoint."""

        @self.router.get(
            "/info",
            response_model=Info,
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={
                200: {
                    "description": "Return dataset's basic info or the list of available bands."
                }
            },
        )
        def info(
            src_path=Depends(self.path_dependency),
            bands_params=Depends(BandsParams),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Return dataset's basic info or the list of available bands."""
            with rasterio.Env(**self.gdal_config):
                with self.reader(src_path, **self.reader_options) as src_dst:
                    return src_dst.info(**bands_params.kwargs, **kwargs)

        @self.router.get(
            "/info.geojson",
            response_model=Feature,
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
            bands_params=Depends(BandsParams),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Return dataset's basic info as a GeoJSON feature."""
            with rasterio.Env(**self.gdal_config):
                with self.reader(src_path, **self.reader_options) as src_dst:
                    info = {
                        "dataset": src_path,
                        **src_dst.info(**bands_params.kwargs, **kwargs).dict(
                            exclude_none=True
                        ),
                    }
                    return bbox_to_feature(src_dst.bounds, properties=info)

        @self.router.get(
            "/bands",
            response_model=List[str],
            responses={200: {"description": "Return a list of supported bands."}},
        )
        def available_bands(
            src_path=Depends(self.path_dependency),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Return a list of supported bands."""
            with rasterio.Env(**self.gdal_config):
                with self.reader(src_path, **self.reader_options) as src_dst:
                    return src_dst.bands

    def metadata(self):
        """Register /metadata endpoint."""

        @self.router.get(
            "/metadata",
            response_model=Metadata,
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={200: {"description": "Return dataset's metadata."}},
        )
        def metadata(
            src_path=Depends(self.path_dependency),
            bands_params=Depends(BandsParams),
            metadata_params=Depends(self.metadata_dependency),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Return metadata."""
            with rasterio.Env(**self.gdal_config):
                with self.reader(src_path, **self.reader_options) as src_dst:
                    return src_dst.metadata(
                        metadata_params.pmin,
                        metadata_params.pmax,
                        **bands_params.kwargs,
                        **metadata_params.kwargs,
                        **kwargs,
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
