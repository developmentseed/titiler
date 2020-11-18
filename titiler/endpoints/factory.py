"""TiTiler Router factories."""

import abc
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Type, Union
from urllib.parse import urlencode

from cogeo_mosaic.backends import BaseBackend, MosaicBackend
from cogeo_mosaic.models import Info as mosaicInfo
from cogeo_mosaic.mosaic import MosaicJSON
from cogeo_mosaic.utils import get_footprints
from morecantile import TileMatrixSet
from rio_tiler.constants import MAX_THREADS
from rio_tiler.io import BaseReader, COGReader, MultiBaseReader
from rio_tiler.models import Bounds, Info, Metadata

from .. import utils
from ..dependencies import (
    BidxExprParams,
    BidxParams,
    DatasetParams,
    DefaultDependency,
    ImageParams,
    MetadataParams,
    PathParams,
    RenderParams,
    TMSParams,
    WebMercatorTMSParams,
)
from ..errors import BadRequestError
from ..models.mapbox import TileJSON
from ..models.mosaic import CreateMosaicJSON, UpdateMosaicJSON
from ..ressources.enums import ImageType, MimeTypes, PixelSelectionMethod
from ..ressources.responses import XMLResponse
from ..templates import templates

from fastapi import APIRouter, Depends, Path, Query

from starlette.requests import Request
from starlette.responses import Response

default_readers_type = Union[Type[BaseReader], Type[MultiBaseReader]]
default_deps_type = Type[DefaultDependency]
img_endpoint_params: Dict[str, Any] = {
    "responses": {
        200: {
            "content": {
                "image/png": {},
                "image/jpeg": {},
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
class BaseFactory(metaclass=abc.ABCMeta):
    """BaseTiler Factory."""

    reader: default_readers_type = field(default=COGReader)
    reader_options: Dict = field(default_factory=dict)

    # FastAPI router
    router: APIRouter = field(default_factory=APIRouter)

    # Path Dependency
    path_dependency: Type[PathParams] = field(default=PathParams)

    # Rasterio Dataset Options (nodata, unscale, resampling)
    dataset_dependency: default_deps_type = field(default=DatasetParams)

    # Indexes/Expression Dependencies
    layer_dependency: default_deps_type = field(default=BidxExprParams)

    # Image rendering Dependencies
    render_dependency: default_deps_type = field(default=RenderParams)

    # TileMatrixSet dependency
    tms_dependency: Callable[..., TileMatrixSet] = WebMercatorTMSParams

    # provide custom dependency
    additional_dependency: Callable[..., Dict] = field(default=lambda: dict())

    # Router Prefix is needed to find the path for /tile if the TilerFactory.router is mounted
    # with other router (multiple `.../tile` routes).
    # e.g if you mount the route with `/cog` prefix, set router_prefix to cog and
    router_prefix: str = ""

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
class TilerFactory(BaseFactory):
    """Tiler Factory."""

    # Endpoint Dependencies
    metadata_dependency: default_deps_type = MetadataParams
    img_dependency: default_deps_type = ImageParams

    # TileMatrixSet dependency
    tms_dependency: Callable[..., TileMatrixSet] = TMSParams

    # Add/Remove some endpoints
    add_preview: bool = True
    add_part: bool = True

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
            with self.reader(src_path.url, **self.reader_options) as src_dst:
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
            """Return basic info."""
            with self.reader(src_path.url, **self.reader_options) as src_dst:
                return src_dst.info(**kwargs)

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
            with self.reader(src_path.url, **self.reader_options) as src_dst:
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
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Create map tile from a dataset."""
            timings = []
            headers: Dict[str, str] = {}

            tilesize = scale * 256

            with utils.Timer() as t:
                with self.reader(
                    src_path.url, tms=tms, **self.reader_options
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
                    colormap = render_params.colormap or getattr(
                        src_dst, "colormap", None
                    )
            timings.append(("dataread", round(t.elapsed * 1000, 2)))

            if not format:
                format = ImageType.jpeg if data.mask.all() else ImageType.png

            with utils.Timer() as t:
                image = data.post_process(
                    in_range=render_params.rescale_range,
                    color_formula=render_params.color_formula,
                )
            timings.append(("postprocess", round(t.elapsed * 1000, 2)))

            with utils.Timer() as t:
                content = image.render(
                    add_mask=render_params.return_mask,
                    img_format=format.driver,
                    colormap=colormap,
                    **format.profile,
                )
            timings.append(("format", round(t.elapsed * 1000, 2)))

            headers["Server-Timing"] = ", ".join(
                [f"{name};dur={time}" for (name, time) in timings]
            )

            return Response(content, media_type=format.mimetype, headers=headers)

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

            q = dict(request.query_params)
            q.pop("TileMatrixSetId", None)
            q.pop("tile_format", None)
            q.pop("tile_scale", None)
            q.pop("minzoom", None)
            q.pop("maxzoom", None)
            qs = urlencode(list(q.items()))
            tiles_url += f"?{qs}"

            with self.reader(src_path.url, tms=tms, **self.reader_options) as src_dst:
                center = list(src_dst.center)
                if minzoom:
                    center[-1] = minzoom
                tjson = {
                    "bounds": src_dst.bounds,
                    "center": tuple(center),
                    "minzoom": minzoom if minzoom is not None else src_dst.minzoom,
                    "maxzoom": maxzoom if maxzoom is not None else src_dst.maxzoom,
                    "name": os.path.basename(src_path.url),
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

            q = dict(request.query_params)
            q.pop("TileMatrixSetId", None)
            q.pop("tile_format", None)
            q.pop("tile_scale", None)
            q.pop("minzoom", None)
            q.pop("maxzoom", None)
            q.pop("SERVICE", None)
            q.pop("REQUEST", None)
            qs = urlencode(list(q.items()))
            tiles_url += f"?{qs}"

            with self.reader(src_path.url, tms=tms, **self.reader_options) as src_dst:
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
                    "media_type": tile_format.mimetype,
                },
                media_type=MimeTypes.xml.value,
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

            with utils.Timer() as t:
                with self.reader(src_path.url, **self.reader_options) as src_dst:
                    values = src_dst.point(
                        lon,
                        lat,
                        **layer_params.kwargs,
                        **dataset_params.kwargs,
                        **kwargs,
                    )
            timings.append(("dataread", round(t.elapsed * 1000, 2)))

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
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Create preview of a dataset."""
            timings = []
            headers: Dict[str, str] = {}

            with utils.Timer() as t:
                with self.reader(src_path.url, **self.reader_options) as src_dst:
                    data = src_dst.preview(
                        **layer_params.kwargs,
                        **img_params.kwargs,
                        **dataset_params.kwargs,
                        **kwargs,
                    )
                    colormap = render_params.colormap or getattr(
                        src_dst, "colormap", None
                    )
            timings.append(("dataread", round(t.elapsed * 1000, 2)))

            if not format:
                format = ImageType.jpeg if data.mask.all() else ImageType.png

            with utils.Timer() as t:
                image = data.post_process(
                    in_range=render_params.rescale_range,
                    color_formula=render_params.color_formula,
                )
            timings.append(("postprocess", round(t.elapsed * 1000, 2)))

            with utils.Timer() as t:
                content = image.render(
                    add_mask=render_params.return_mask,
                    img_format=format.driver,
                    colormap=colormap,
                    **format.profile,
                )
            timings.append(("format", round(t.elapsed * 1000, 2)))

            if timings:
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            return Response(content, media_type=format.mimetype, headers=headers)

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
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Create image from part of a dataset."""
            timings = []
            headers: Dict[str, str] = {}

            with utils.Timer() as t:
                with self.reader(src_path.url, **self.reader_options) as src_dst:
                    data = src_dst.part(
                        [minx, miny, maxx, maxy],
                        **layer_params.kwargs,
                        **image_params.kwargs,
                        **dataset_params.kwargs,
                        **kwargs,
                    )
                    colormap = render_params.colormap or getattr(
                        src_dst, "colormap", None
                    )
            timings.append(("dataread", round(t.elapsed * 1000, 2)))

            with utils.Timer() as t:
                image = data.post_process(
                    in_range=render_params.rescale_range,
                    color_formula=render_params.color_formula,
                )
            timings.append(("postprocess", round(t.elapsed * 1000, 2)))

            with utils.Timer() as t:
                content = image.render(
                    add_mask=render_params.return_mask,
                    img_format=format.driver,
                    colormap=colormap,
                    **format.profile,
                )
            timings.append(("format", round(t.elapsed * 1000, 2)))

            if timings:
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            return Response(content, media_type=format.mimetype, headers=headers)


@dataclass
class MosaicTilerFactory(BaseFactory):
    """
    MosaicTiler Factory.

    The main difference with titiler.endpoint.factory.TilerFactory is that this factory
    needs a reader (MosaicBackend) and a dataset_reader (BaseReader).
    """

    reader: BaseBackend = field(default=MosaicBackend)
    dataset_reader: Type[BaseReader] = field(default=COGReader)

    # BaseBackend does not support other TMS than WebMercator
    tms_dependency: Callable[..., TileMatrixSet] = WebMercatorTMSParams

    # Add/Remove some endpoints
    add_create: bool = True
    add_update: bool = True

    def register_routes(self):
        """
        This Method register routes to the router.

        Because we wrap the endpoints in a class we cannot define the routes as
        methods (because of the self argument). The HACK is to define routes inside
        the class method and register them after the class initialisation.

        """

        self.read()
        if self.add_create:
            self.create()
        if self.add_update:
            self.update()

        self.bounds()
        self.info()
        self.tile()
        self.tilejson()
        self.wmts()
        self.point()

    ############################################################################
    # /read
    ############################################################################
    def read(self):
        """Register / (Get) Read endpoint."""

        @self.router.get(
            "",
            response_model=MosaicJSON,
            response_model_exclude_none=True,
            responses={200: {"description": "Return MosaicJSON definition"}},
        )
        def read(src_path=Depends(self.path_dependency),):
            """Read a MosaicJSON"""
            with self.reader(src_path.url) as mosaic:
                return mosaic.mosaic_def

    ############################################################################
    # /create
    ############################################################################
    def create(self):
        """Register / (POST) Create endpoint."""

        @self.router.post(
            "", response_model=MosaicJSON, response_model_exclude_none=True
        )
        def create(body: CreateMosaicJSON):
            """Create a MosaicJSON"""
            mosaic = MosaicJSON.from_urls(
                body.files,
                minzoom=body.minzoom,
                maxzoom=body.maxzoom,
                max_threads=body.max_threads,
            )
            src_path = self.path_dependency(body.url)
            with self.reader(
                src_path.url, mosaic_def=mosaic, reader=self.dataset_reader
            ) as mosaic:
                try:
                    mosaic.write()
                except NotImplementedError:
                    raise BadRequestError(
                        f"{mosaic.__class__.__name__} does not support write operations"
                    )
                return mosaic.mosaic_def

    ############################################################################
    # /update
    ############################################################################
    def update(self):
        """Register / (PUST) Update endpoint."""

        @self.router.put(
            "", response_model=MosaicJSON, response_model_exclude_none=True
        )
        def update_mosaicjson(body: UpdateMosaicJSON):
            """Update an existing MosaicJSON"""
            src_path = self.path_dependency(body.url)
            with self.reader(src_path.url, reader=self.dataset_reader) as mosaic:
                features = get_footprints(body.files, max_threads=body.max_threads)
                try:
                    mosaic.update(features, add_first=body.add_first, quiet=True)
                except NotImplementedError:
                    raise BadRequestError(
                        f"{mosaic.__class__.__name__} does not support update operations"
                    )
                return mosaic.mosaic_def

    ############################################################################
    # /bounds
    ############################################################################
    def bounds(self):
        """Register /bounds endpoint."""

        @self.router.get(
            "/bounds",
            response_model=Bounds,
            responses={200: {"description": "Return the bounds of the MosaicJSON"}},
        )
        def bounds(src_path=Depends(self.path_dependency)):
            """Return the bounds of the COG."""
            with self.reader(src_path.url) as src_dst:
                return {"bounds": src_dst.bounds}

    ############################################################################
    # /info
    ############################################################################
    def info(self):
        """Register /info endpoint"""

        @self.router.get(
            "/info",
            response_model=mosaicInfo,
            responses={200: {"description": "Return info about the MosaicJSON"}},
        )
        def info(src_path=Depends(self.path_dependency)):
            """Return basic info."""
            with self.reader(src_path.url) as src_dst:
                return src_dst.info()

    ############################################################################
    # /tiles
    ############################################################################
    def tile(self):  # noqa: C901
        """Register /tiles endpoints."""

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
            pixel_selection: PixelSelectionMethod = Query(
                PixelSelectionMethod.first, description="Pixel selection method."
            ),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Create map tile from a COG."""
            timings = []
            headers: Dict[str, str] = {}

            tilesize = scale * 256

            threads = int(os.getenv("MOSAIC_CONCURRENCY", MAX_THREADS))
            with utils.Timer() as t:
                with self.reader(
                    src_path.url,
                    reader=self.dataset_reader,
                    reader_options=self.reader_options,
                ) as src_dst:
                    mosaic_read = t.from_start
                    timings.append(("mosaicread", round(mosaic_read * 1000, 2)))

                    data, _ = src_dst.tile(
                        x,
                        y,
                        z,
                        pixel_selection=pixel_selection.method(),
                        threads=threads,
                        tilesize=tilesize,
                        **layer_params.kwargs,
                        **dataset_params.kwargs,
                        **kwargs,
                    )
            timings.append(("dataread", round((t.elapsed - mosaic_read) * 1000, 2)))

            if not format:
                format = ImageType.jpeg if data.mask.all() else ImageType.png

            with utils.Timer() as t:
                image = data.post_process(
                    in_range=render_params.rescale_range,
                    color_formula=render_params.color_formula,
                )
            timings.append(("postprocess", round(t.elapsed * 1000, 2)))

            with utils.Timer() as t:
                content = image.render(
                    add_mask=render_params.return_mask,
                    img_format=format.driver,
                    colormap=render_params.colormap,
                    **format.profile,
                )
            timings.append(("format", round(t.elapsed * 1000, 2)))

            headers["Server-Timing"] = ", ".join(
                [f"{name};dur={time}" for (name, time) in timings]
            )

            headers["X-Assets"] = ",".join(data.assets)

            return Response(content, media_type=format.mimetype, headers=headers)

    def tilejson(self):  # noqa: C901
        """Add tilejson endpoint."""

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
            pixel_selection: PixelSelectionMethod = Query(
                PixelSelectionMethod.first, description="Pixel selection method."
            ),  # noqa
            kwargs: Dict = Depends(self.additional_dependency),  # noqa
        ):
            """Return TileJSON document for a COG."""
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

            q = dict(request.query_params)
            q.pop("TileMatrixSetId", None)
            q.pop("tile_format", None)
            q.pop("tile_scale", None)
            q.pop("minzoom", None)
            q.pop("maxzoom", None)
            qs = urlencode(list(q.items()))
            tiles_url += f"?{qs}"

            with self.reader(src_path.url) as src_dst:
                center = list(src_dst.center)
                if minzoom:
                    center[-1] = minzoom
                tjson = {
                    "bounds": src_dst.bounds,
                    "center": tuple(center),
                    "minzoom": minzoom if minzoom is not None else src_dst.minzoom,
                    "maxzoom": maxzoom if maxzoom is not None else src_dst.maxzoom,
                    "name": os.path.basename(src_path.url),
                    "tiles": [tiles_url],
                }

            return tjson

    def wmts(self):  # noqa: C901
        """Add wmts endpoint."""

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
            pixel_selection: PixelSelectionMethod = Query(
                PixelSelectionMethod.first, description="Pixel selection method."
            ),  # noqa
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

            q = dict(request.query_params)
            q.pop("TileMatrixSetId", None)
            q.pop("tile_format", None)
            q.pop("tile_scale", None)
            q.pop("minzoom", None)
            q.pop("maxzoom", None)
            q.pop("SERVICE", None)
            q.pop("REQUEST", None)
            qs = urlencode(list(q.items()))
            tiles_url += f"?{qs}"

            with self.reader(src_path.url) as src_dst:
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
                    "media_type": tile_format.mimetype,
                },
                media_type=MimeTypes.xml.value,
            )

    ############################################################################
    # /point (Optional)
    ############################################################################
    def point(self):
        """Register /point endpoint."""

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
            """Get Point value for a Mosaic."""
            timings = []
            threads = int(os.getenv("MOSAIC_CONCURRENCY", MAX_THREADS))

            with utils.Timer() as t:
                with self.reader(
                    src_path.url,
                    reader=self.dataset_reader,
                    reader_options=self.reader_options,
                ) as src_dst:
                    mosaic_read = t.from_start
                    timings.append(("mosaicread", round(mosaic_read * 1000, 2)))
                    values = src_dst.point(
                        lon,
                        lat,
                        threads=threads,
                        **layer_params.kwargs,
                        **dataset_params.kwargs,
                        **kwargs,
                    )
            timings.append(("dataread", round((t.elapsed - mosaic_read) * 1000, 2)))

            response.headers["Server-Timing"] = ", ".join(
                [f"{name};dur={time}" for (name, time) in timings]
            )

            return {"coordinates": [lon, lat], "values": values}
