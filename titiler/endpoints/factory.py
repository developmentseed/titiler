"""TiTiler Router factories."""

import abc
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Type, Union
from urllib.parse import urlencode

import pkg_resources
from cogeo_mosaic.backends import BaseBackend, MosaicBackend
from cogeo_mosaic.mosaic import MosaicJSON
from cogeo_mosaic.utils import get_footprints
from rasterio.transform import from_bounds
from rio_tiler.constants import MAX_THREADS, WGS84_CRS
from rio_tiler.io import BaseReader, COGReader, MultiBaseReader
from rio_tiler_crs import COGReader as TMSCOGReader

from .. import utils
from ..dependencies import (
    DefaultDependency,
    ImageParams,
    MetadataParams,
    PathParams,
    PointParams,
    TileParams,
    TMSParams,
    WebMercatorTMSParams,
)
from ..errors import BadRequestError, TileNotFoundError
from ..models.dataset import Bounds, Info, Metadata
from ..models.mapbox import TileJSON
from ..models.mosaic import CreateMosaicJSON, UpdateMosaicJSON, mosaicInfo
from ..ressources.common import img_endpoint_params
from ..ressources.enums import (  # fmt: off
    ImageMimeTypes,
    ImageType,
    MimeTypes,
    PixelSelectionMethod,
)
from ..ressources.responses import XMLResponse

from fastapi import APIRouter, Depends, Path, Query

from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates

template_dir = pkg_resources.resource_filename("titiler", "templates")
templates = Jinja2Templates(directory=template_dir)

default_readers_type = Union[Type[BaseReader], Type[MultiBaseReader]]


# ref: https://github.com/python/mypy/issues/5374
@dataclass  # type: ignore
class BaseFactory(metaclass=abc.ABCMeta):
    """BaseTiler Factory."""

    reader: default_readers_type = field(default=COGReader)
    reader_options: Dict = field(default_factory=dict)

    # FastAPI router
    router: APIRouter = field(default_factory=APIRouter)

    # Endpoint Dependencies
    path_dependency: Type[PathParams] = field(default=PathParams)
    tiles_dependency: Type[TileParams] = field(default=TileParams)
    point_dependency: Type[PointParams] = field(default=PointParams)

    tms_dependency: Callable = WebMercatorTMSParams

    # provide custom dependency
    additional_dependency: Type[DefaultDependency] = field(default=DefaultDependency)

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
    metadata_dependency: Type[MetadataParams] = MetadataParams
    img_dependency: Type[ImageParams] = ImageParams

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
        self._bounds()
        self._info()
        self._metadata()
        self._tile()
        self._point()

        if self.add_preview:
            self._preview()

        if self.add_part:
            self._part()

    ############################################################################
    # /bounds
    ############################################################################
    def _bounds(self):
        """Register /bounds endpoint to router."""

        @self.router.get(
            "/bounds",
            response_model=Bounds,
            responses={200: {"description": "Return dataset's bounds."}},
        )
        def bounds(src_path=Depends(self.path_dependency)):
            """Return the bounds of the COG."""
            reader = src_path.reader or self.reader
            with reader(src_path.url, **self.reader_options) as src_dst:
                return {"bounds": src_dst.bounds}

    ############################################################################
    # /info
    ############################################################################
    def _info(self):
        """Register /info endpoint to router."""

        @self.router.get(
            "/info",
            response_model=Info,
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={200: {"description": "Return dataset's basic info."}},
        )
        def info(
            src_path=Depends(self.path_dependency),
            options=Depends(self.additional_dependency),
        ):
            """Return basic info."""
            reader = src_path.reader or self.reader
            with reader(src_path.url, **self.reader_options) as src_dst:
                info = src_dst.info(**options.kwargs)
            return info

    ############################################################################
    # /metadata
    ############################################################################
    def _metadata(self):
        """Register /metadata endpoint to router."""

        @self.router.get(
            "/metadata",
            response_model=Metadata,
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={200: {"description": "Return dataset's metadata."}},
        )
        def metadata(
            src_path=Depends(self.path_dependency),
            params=Depends(self.metadata_dependency),
            options=Depends(self.additional_dependency),
        ):
            """Return metadata."""
            reader = src_path.reader or self.reader
            with reader(src_path.url, **self.reader_options) as src_dst:
                kwargs = options.kwargs.copy()
                if params.nodata is not None:
                    kwargs["nodata"] = params.nodata
                info = src_dst.metadata(
                    params.pmin,
                    params.pmax,
                    indexes=params.indexes,
                    max_size=params.max_size,
                    hist_options=params.hist_options,
                    bounds=params.bounds,
                    resampling_method=params.resampling_method.name,
                    **kwargs,
                )
            return info

    ############################################################################
    # /tiles
    ############################################################################
    def _tile(self):  # noqa: C901
        tile_endpoint_params = img_endpoint_params.copy()

        @self.router.get(r"/tiles/{z}/{x}/{y}", **tile_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}.{format}", **tile_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}@{scale}x", **tile_endpoint_params)
        @self.router.get(
            r"/tiles/{z}/{x}/{y}@{scale}x.{format}", **tile_endpoint_params
        )
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}", **tile_endpoint_params
        )
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}.{format}", **tile_endpoint_params
        )
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x", **tile_endpoint_params
        )
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
            **tile_endpoint_params,
        )
        def tile(
            z: int = Path(..., ge=0, le=30, description="Mercator tiles's zoom level"),
            x: int = Path(..., description="Mercator tiles's column"),
            y: int = Path(..., description="Mercator tiles's row"),
            tms=Depends(self.tms_dependency),
            scale: int = Query(
                1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
            ),
            format: ImageType = Query(
                None, description="Output image type. Default is auto."
            ),
            src_path=Depends(self.path_dependency),
            params=Depends(self.tiles_dependency),
            options=Depends(self.additional_dependency),
        ):
            """Create map tile from a dataset."""
            timings = []
            headers: Dict[str, str] = {}

            tilesize = scale * 256

            with utils.Timer() as t:
                reader = src_path.reader or self.reader
                with reader(src_path.url, **self.reader_options) as src_dst:
                    kwargs = options.kwargs.copy()
                    if params.nodata is not None:
                        kwargs["nodata"] = params.nodata
                    tile, mask = src_dst.tile(
                        x,
                        y,
                        z,
                        tilesize=tilesize,
                        indexes=params.indexes,
                        expression=params.expression,
                        resampling_method=params.resampling_method.name,
                        **kwargs,
                    )
                    colormap = params.colormap or getattr(src_dst, "colormap", None)

            timings.append(("Read", t.elapsed))

            if not format:
                format = ImageType.jpg if mask.all() else ImageType.png

            with utils.Timer() as t:
                tile = utils.postprocess(
                    tile,
                    mask,
                    rescale=params.rescale,
                    color_formula=params.color_formula,
                )
            timings.append(("Post-process", t.elapsed))

            bounds = tms.xy_bounds(x, y, z)
            dst_transform = from_bounds(*bounds, tilesize, tilesize)
            with utils.Timer() as t:
                content = utils.reformat(
                    tile,
                    mask,
                    format,
                    colormap=colormap,
                    transform=dst_transform,
                    crs=tms.crs,
                )
            timings.append(("Format", t.elapsed))

            if timings:
                headers["X-Server-Timings"] = "; ".join(
                    [
                        "{} - {:0.2f}".format(name, time * 1000)
                        for (name, time) in timings
                    ]
                )

            return Response(
                content, media_type=ImageMimeTypes[format.value].value, headers=headers,
            )

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
            tms=Depends(self.tms_dependency),
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
            params=Depends(self.tiles_dependency),  # noqa
            options=Depends(self.additional_dependency),  # noqa
        ):
            """Return TileJSON document for a dataset."""
            kwargs = {
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
                "scale": tile_scale,
                "TileMatrixSetId": tms.identifier,
            }
            if tile_format:
                kwargs["format"] = tile_format.value
            tiles_url = self.url_for(request, "tile", **kwargs)

            q = dict(request.query_params)
            q.pop("TileMatrixSetId", None)
            q.pop("tile_format", None)
            q.pop("tile_scale", None)
            q.pop("minzoom", None)
            q.pop("maxzoom", None)
            qs = urlencode(list(q.items()))
            tiles_url += f"?{qs}"

            reader = src_path.reader or self.reader
            with reader(src_path.url, **self.reader_options) as src_dst:
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

        @self.router.get("/WMTSCapabilities.xml", response_class=XMLResponse)
        @self.router.get(
            "/{TileMatrixSetId}/WMTSCapabilities.xml", response_class=XMLResponse
        )
        def wmts(
            request: Request,
            tms=Depends(self.tms_dependency),
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
            params=Depends(self.tiles_dependency),  # noqa
            options=Depends(self.additional_dependency),  # noqa
        ):
            """OGC WMTS endpoint."""
            kwargs = {
                "z": "{TileMatrix}",
                "x": "{TileCol}",
                "y": "{TileRow}",
                "scale": tile_scale,
                "format": tile_format.value,
                "TileMatrixSetId": tms.identifier,
            }
            tiles_url = self.url_for(request, "tile", **kwargs)

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

            reader = src_path.reader or self.reader
            with reader(src_path.url, **self.reader_options) as src_dst:
                bounds = src_dst.bounds
                minzoom = minzoom if minzoom is not None else src_dst.minzoom
                maxzoom = maxzoom if maxzoom is not None else src_dst.maxzoom

            media_type = ImageMimeTypes[tile_format.value].value

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
                    "media_type": media_type,
                },
                media_type=MimeTypes.xml.value,
            )

    ############################################################################
    # /point
    ############################################################################
    def _point(self):
        @self.router.get(
            r"/point/{lon},{lat}",
            responses={200: {"description": "Return a value for a point"}},
        )
        def point(
            lon: float = Path(..., description="Longitude"),
            lat: float = Path(..., description="Latitude"),
            src_path=Depends(self.path_dependency),
            params=Depends(self.point_dependency),
            options=Depends(self.additional_dependency),
        ):
            """Get Point value for a dataset."""
            timings = []
            headers: Dict[str, str] = {}

            with utils.Timer() as t:
                reader = src_path.reader or self.reader
                with reader(src_path.url, **self.reader_options) as src_dst:
                    kwargs = options.kwargs.copy()
                    if params.nodata is not None:
                        kwargs["nodata"] = params.nodata
                    values = src_dst.point(
                        lon,
                        lat,
                        indexes=params.indexes,
                        expression=params.expression,
                        **kwargs,
                    )
            timings.append(("Read", t.elapsed))

            if timings:
                headers["X-Server-Timings"] = "; ".join(
                    [
                        "{} - {:0.2f}".format(name, time * 1000)
                        for (name, time) in timings
                    ]
                )

            return {"coordinates": [lon, lat], "values": values}

    ############################################################################
    # /preview (Optional)
    ############################################################################
    def _preview(self):
        prev_endpoint_params = img_endpoint_params.copy()

        @self.router.get(r"/preview", **prev_endpoint_params)
        @self.router.get(r"/preview.{format}", **prev_endpoint_params)
        def preview(
            format: ImageType = Query(
                None, description="Output image type. Default is auto."
            ),
            src_path=Depends(self.path_dependency),
            params=Depends(self.img_dependency),
            options=Depends(self.additional_dependency),
        ):
            """Create preview of a dataset."""
            timings = []
            headers: Dict[str, str] = {}

            with utils.Timer() as t:
                reader = src_path.reader or self.reader
                with reader(src_path.url, **self.reader_options) as src_dst:
                    kwargs = options.kwargs.copy()
                    if params.nodata is not None:
                        kwargs["nodata"] = params.nodata
                    data, mask = src_dst.preview(
                        height=params.height,
                        width=params.width,
                        max_size=params.max_size,
                        indexes=params.indexes,
                        expression=params.expression,
                        resampling_method=params.resampling_method.name,
                        **options.kwargs,
                    )
                    colormap = params.colormap or getattr(src_dst, "colormap", None)
            timings.append(("Read", t.elapsed))

            if not format:
                format = ImageType.jpg if mask.all() else ImageType.png

            with utils.Timer() as t:
                data = utils.postprocess(
                    data,
                    mask,
                    rescale=params.rescale,
                    color_formula=params.color_formula,
                )
            timings.append(("Post-process", t.elapsed))

            with utils.Timer() as t:
                content = utils.reformat(data, mask, format, colormap=colormap)
            timings.append(("Format", t.elapsed))

            if timings:
                headers["X-Server-Timings"] = "; ".join(
                    [
                        "{} - {:0.2f}".format(name, time * 1000)
                        for (name, time) in timings
                    ]
                )

            return Response(
                content, media_type=ImageMimeTypes[format.value].value, headers=headers,
            )

    ############################################################################
    # /crop (Optional)
    ############################################################################
    def _part(self):
        part_endpoint_params = img_endpoint_params.copy()

        # @router.get(r"/crop/{minx},{miny},{maxx},{maxy}", **part_endpoint_params)
        @self.router.get(
            r"/crop/{minx},{miny},{maxx},{maxy}.{format}", **part_endpoint_params,
        )
        def part(
            minx: float = Path(..., description="Bounding box min X"),
            miny: float = Path(..., description="Bounding box min Y"),
            maxx: float = Path(..., description="Bounding box max X"),
            maxy: float = Path(..., description="Bounding box max Y"),
            format: ImageType = Query(None, description="Output image type."),
            src_path=Depends(self.path_dependency),
            params=Depends(self.img_dependency),
            options=Depends(self.additional_dependency),
        ):
            """Create image from part of a dataset."""
            timings = []
            headers: Dict[str, str] = {}

            with utils.Timer() as t:
                reader = src_path.reader or self.reader
                with reader(src_path.url, **self.reader_options) as src_dst:
                    kwargs = options.kwargs.copy()
                    if params.nodata is not None:
                        kwargs["nodata"] = params.nodata
                    data, mask = src_dst.part(
                        [minx, miny, maxx, maxy],
                        height=params.height,
                        width=params.width,
                        max_size=params.max_size,
                        indexes=params.indexes,
                        expression=params.expression,
                        resampling_method=params.resampling_method.name,
                        **kwargs,
                    )
                    colormap = params.colormap or getattr(src_dst, "colormap", None)
            timings.append(("Read", t.elapsed))

            if not format:
                format = ImageType.jpg if mask.all() else ImageType.png

            with utils.Timer() as t:
                data = utils.postprocess(
                    data,
                    mask,
                    rescale=params.rescale,
                    color_formula=params.color_formula,
                )
            timings.append(("Post-process", t.elapsed))

            with utils.Timer() as t:
                dst_transform = from_bounds(
                    minx, miny, maxx, maxy, data.shape[2], data.shape[1]
                )
                content = utils.reformat(
                    data,
                    mask,
                    format,
                    colormap=colormap,
                    transform=dst_transform,
                    crs=WGS84_CRS,
                )
            timings.append(("Format", t.elapsed))

            if timings:
                headers["X-Server-Timings"] = "; ".join(
                    [
                        "{} - {:0.2f}".format(name, time * 1000)
                        for (name, time) in timings
                    ]
                )

            return Response(
                content, media_type=ImageMimeTypes[format.value].value, headers=headers,
            )


@dataclass
class TMSTilerFactory(TilerFactory):
    """Tiler Factory with TMS."""

    reader: default_readers_type = field(default=TMSCOGReader)
    tms_dependency: Callable = TMSParams

    ############################################################################
    # /tiles
    ############################################################################
    def _tile(self):  # noqa: C901
        tile_endpoint_params = img_endpoint_params.copy()

        @self.router.get(r"/tiles/{z}/{x}/{y}", **tile_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}.{format}", **tile_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}@{scale}x", **tile_endpoint_params)
        @self.router.get(
            r"/tiles/{z}/{x}/{y}@{scale}x.{format}", **tile_endpoint_params
        )
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}", **tile_endpoint_params
        )
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}.{format}", **tile_endpoint_params
        )
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x", **tile_endpoint_params
        )
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
            **tile_endpoint_params,
        )
        def tile(
            z: int = Path(..., ge=0, le=30, description="Mercator tiles's zoom level"),
            x: int = Path(..., description="Mercator tiles's column"),
            y: int = Path(..., description="Mercator tiles's row"),
            tms=Depends(self.tms_dependency),
            scale: int = Query(
                1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
            ),
            format: ImageType = Query(
                None, description="Output image type. Default is auto."
            ),
            src_path=Depends(self.path_dependency),
            params=Depends(self.tiles_dependency),
            options=Depends(self.additional_dependency),
        ):
            """Create map tile from a dataset."""
            timings = []
            headers: Dict[str, str] = {}

            tilesize = scale * 256

            with utils.Timer() as t:
                reader = src_path.reader or self.reader
                with reader(src_path.url, tms=tms, **self.reader_options) as src_dst:
                    kwargs = options.kwargs.copy()
                    if params.nodata is not None:
                        kwargs["nodata"] = params.nodata
                    tile, mask = src_dst.tile(
                        x,
                        y,
                        z,
                        tilesize=tilesize,
                        indexes=params.indexes,
                        expression=params.expression,
                        resampling_method=params.resampling_method.name,
                        **kwargs,
                    )
                    colormap = params.colormap or getattr(src_dst, "colormap", None)

            timings.append(("Read", t.elapsed))

            if not format:
                format = ImageType.jpg if mask.all() else ImageType.png

            with utils.Timer() as t:
                tile = utils.postprocess(
                    tile,
                    mask,
                    rescale=params.rescale,
                    color_formula=params.color_formula,
                )
            timings.append(("Post-process", t.elapsed))

            bounds = tms.xy_bounds(x, y, z)
            dst_transform = from_bounds(*bounds, tilesize, tilesize)
            with utils.Timer() as t:
                content = utils.reformat(
                    tile,
                    mask,
                    format,
                    colormap=colormap,
                    transform=dst_transform,
                    crs=tms.crs,
                )
            timings.append(("Format", t.elapsed))

            if timings:
                headers["X-Server-Timings"] = "; ".join(
                    [
                        "{} - {:0.2f}".format(name, time * 1000)
                        for (name, time) in timings
                    ]
                )

            return Response(
                content, media_type=ImageMimeTypes[format.value].value, headers=headers,
            )

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
            tms=Depends(self.tms_dependency),
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
            params=Depends(self.tiles_dependency),  # noqa
            options=Depends(self.additional_dependency),  # noqa
        ):
            """Return TileJSON document for a dataset."""
            kwargs = {
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
                "scale": tile_scale,
                "TileMatrixSetId": tms.identifier,
            }
            if tile_format:
                kwargs["format"] = tile_format.value
            tiles_url = self.url_for(request, "tile", **kwargs)

            q = dict(request.query_params)
            q.pop("TileMatrixSetId", None)
            q.pop("tile_format", None)
            q.pop("tile_scale", None)
            q.pop("minzoom", None)
            q.pop("maxzoom", None)
            qs = urlencode(list(q.items()))
            tiles_url += f"?{qs}"

            reader = src_path.reader or self.reader
            with reader(src_path.url, tms=tms, **self.reader_options) as src_dst:
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

        @self.router.get("/WMTSCapabilities.xml", response_class=XMLResponse)
        @self.router.get(
            "/{TileMatrixSetId}/WMTSCapabilities.xml", response_class=XMLResponse
        )
        def wmts(
            request: Request,
            tms=Depends(self.tms_dependency),
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
            params=Depends(self.tiles_dependency),  # noqa
            options=Depends(self.additional_dependency),  # noqa
        ):
            """OGC WMTS endpoint."""
            kwargs = {
                "z": "{TileMatrix}",
                "x": "{TileCol}",
                "y": "{TileRow}",
                "scale": tile_scale,
                "format": tile_format.value,
                "TileMatrixSetId": tms.identifier,
            }
            tiles_url = self.url_for(request, "tile", **kwargs)

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

            reader = src_path.reader or self.reader
            with reader(src_path.url, tms=tms, **self.reader_options) as src_dst:
                bounds = src_dst.bounds
                minzoom = minzoom if minzoom is not None else src_dst.minzoom
                maxzoom = maxzoom if maxzoom is not None else src_dst.maxzoom

            media_type = ImageMimeTypes[tile_format.value].value

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
                    "media_type": media_type,
                },
                media_type=MimeTypes.xml.value,
            )


@dataclass
class MosaicTilerFactory(BaseFactory):
    """
    MosaicTiler Factory.

    The main difference with titiler.endpoint.factory.TilerFactory is that this factory
    needs a reader (MosaicBackend) and a dataset_reader (BaseReader).
    """

    reader: BaseBackend = field(default=MosaicBackend)
    dataset_reader: BaseReader = field(default=COGReader)

    # BaseBackend does not support other TMS than WebMercator
    tms_dependency: Callable = field(default=WebMercatorTMSParams)

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

        self._read()
        if self.add_create:
            self._create()
        if self.add_update:
            self._update()

        self._bounds()
        self._info()
        self._tile()
        self._point()

    ############################################################################
    # /read
    ############################################################################
    def _read(self):
        """Add / - GET (Read) route."""

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
    def _create(self):
        """Add / - POST (create) route."""

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
            reader = src_path.reader or self.dataset_reader
            with self.reader(src_path.url, mosaic_def=mosaic, reader=reader) as mosaic:
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
    def _update(self):
        """Add / - PUT (update) route."""

        @self.router.put(
            "", response_model=MosaicJSON, response_model_exclude_none=True
        )
        def update_mosaicjson(body: UpdateMosaicJSON):
            """Update an existing MosaicJSON"""
            src_path = self.path_dependency(body.url)
            reader = src_path.reader or self.dataset_reader
            with self.reader(src_path.url, reader=reader) as mosaic:
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
    def _bounds(self):
        """Register /bounds endpoint to router."""

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
    def _info(self):
        """Register /info endpoint to router."""

        @self.router.get(
            "/info",
            response_model=mosaicInfo,
            responses={200: {"description": "Return info about the MosaicJSON"}},
        )
        def info(src_path=Depends(self.path_dependency)):
            """Return basic info."""
            with self.reader(src_path.url) as src_dst:
                info = src_dst.info()
            return info

    ############################################################################
    # /tiles
    ############################################################################
    def _tile(self):  # noqa: C901
        tile_endpoint_params = img_endpoint_params.copy()

        @self.router.get(r"/tiles/{z}/{x}/{y}", **tile_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}.{format}", **tile_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}@{scale}x", **tile_endpoint_params)
        @self.router.get(
            r"/tiles/{z}/{x}/{y}@{scale}x.{format}", **tile_endpoint_params
        )
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}", **tile_endpoint_params
        )
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}.{format}", **tile_endpoint_params
        )
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x", **tile_endpoint_params
        )
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
            **tile_endpoint_params,
        )
        def tile(
            z: int = Path(..., ge=0, le=30, description="Mercator tiles's zoom level"),
            x: int = Path(..., description="Mercator tiles's column"),
            y: int = Path(..., description="Mercator tiles's row"),
            tms=Depends(self.tms_dependency),
            scale: int = Query(
                1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
            ),
            format: ImageType = Query(
                None, description="Output image type. Default is auto."
            ),
            src_path=Depends(self.path_dependency),
            params=Depends(self.tiles_dependency),
            options=Depends(self.additional_dependency),
            pixel_selection: PixelSelectionMethod = Query(
                PixelSelectionMethod.first, description="Pixel selection method."
            ),
        ):
            """Create map tile from a COG."""
            timings = []
            headers: Dict[str, str] = {}

            tilesize = scale * 256

            with utils.Timer() as t:
                reader = src_path.reader or self.dataset_reader
                threads = int(os.getenv("MOSAIC_CONCURRENCY", MAX_THREADS))

                with self.reader(
                    src_path.url, reader=reader, reader_options=self.reader_options
                ) as src_dst:
                    kwargs = options.kwargs.copy()
                    if params.nodata is not None:
                        kwargs["nodata"] = params.nodata
                    (data, mask), assets_used = src_dst.tile(
                        x,
                        y,
                        z,
                        pixel_selection=pixel_selection.method(),
                        threads=threads,
                        tilesize=tilesize,
                        indexes=params.indexes,
                        expression=params.expression,
                        resampling_method=params.resampling_method.name,
                        **kwargs,
                    )

            timings.append(("Read-tile", t.elapsed))

            if data is None:
                raise TileNotFoundError(f"Tile {z}/{x}/{y} was not found")

            if not format:
                format = ImageType.jpg if mask.all() else ImageType.png

            with utils.Timer() as t:
                data = utils.postprocess(
                    data,
                    mask,
                    rescale=params.rescale,
                    color_formula=params.color_formula,
                )
            timings.append(("Post-process", t.elapsed))

            bounds = tms.xy_bounds(x, y, z)
            dst_transform = from_bounds(*bounds, tilesize, tilesize)
            with utils.Timer() as t:
                content = utils.reformat(
                    data,
                    mask,
                    format,
                    colormap=params.colormap,
                    transform=dst_transform,
                    crs=tms.crs,
                )
            timings.append(("Format", t.elapsed))

            if timings:
                headers["X-Server-Timings"] = "; ".join(
                    [
                        "{} - {:0.2f}".format(name, time * 1000)
                        for (name, time) in timings
                    ]
                )

            if assets_used:
                headers["X-Assets"] = ",".join(assets_used)

            return Response(
                content, media_type=ImageMimeTypes[format.value].value, headers=headers,
            )

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
            tms=Depends(self.tms_dependency),
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
            params=Depends(self.tiles_dependency),  # noqa
            options=Depends(self.additional_dependency),  # noqa
            pixel_selection: PixelSelectionMethod = Query(
                PixelSelectionMethod.first, description="Pixel selection method."
            ),  # noqa
        ):
            """Return TileJSON document for a COG."""
            kwargs = {
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
                "scale": tile_scale,
                "TileMatrixSetId": tms.identifier,
            }
            if tile_format:
                kwargs["format"] = tile_format.value
            tiles_url = self.url_for(request, "tile", **kwargs)

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

        @self.router.get("/WMTSCapabilities.xml", response_class=XMLResponse)
        @self.router.get(
            "/{TileMatrixSetId}/WMTSCapabilities.xml", response_class=XMLResponse
        )
        def wmts(
            request: Request,
            tms=Depends(self.tms_dependency),
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
            params=Depends(self.tiles_dependency),  # noqa
            options=Depends(self.additional_dependency),  # noqa
            pixel_selection: PixelSelectionMethod = Query(
                PixelSelectionMethod.first, description="Pixel selection method."
            ),  # noqa
        ):
            """OGC WMTS endpoint."""
            kwargs = {
                "z": "{TileMatrix}",
                "x": "{TileCol}",
                "y": "{TileRow}",
                "scale": tile_scale,
                "format": tile_format.value,
                "TileMatrixSetId": tms.identifier,
            }
            tiles_url = self.url_for(request, "tile", **kwargs)

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

            media_type = ImageMimeTypes[tile_format.value].value

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
                    "media_type": media_type,
                },
                media_type=MimeTypes.xml.value,
            )

    ############################################################################
    # /point (Optional)
    ############################################################################
    def _point(self):
        @self.router.get(
            r"/point/{lon},{lat}",
            responses={200: {"description": "Return a value for a point"}},
        )
        def point(
            lon: float = Path(..., description="Longitude"),
            lat: float = Path(..., description="Latitude"),
            src_path=Depends(self.path_dependency),
            params=Depends(self.point_dependency),
            options=Depends(self.additional_dependency),
        ):
            """Get Point value for a Mosaic."""
            timings = []
            headers: Dict[str, str] = {}
            threads = int(os.getenv("MOSAIC_CONCURRENCY", MAX_THREADS))

            with utils.Timer() as t:
                reader = src_path.reader or self.dataset_reader
                with self.reader(
                    src_path.url, reader=reader, reader_options=self.reader_options,
                ) as src_dst:
                    kwargs = options.kwargs.copy()
                    if params.nodata is not None:
                        kwargs["nodata"] = params.nodata
                    values = src_dst.point(
                        lon,
                        lat,
                        threads=threads,
                        indexes=params.indexes,
                        expression=params.expression,
                        **kwargs,
                    )
            timings.append(("Read", t.elapsed))

            if timings:
                headers["X-Server-Timings"] = "; ".join(
                    [
                        "{} - {:0.2f}".format(name, time * 1000)
                        for (name, time) in timings
                    ]
                )

            return {"coordinates": [lon, lat], "values": values}
