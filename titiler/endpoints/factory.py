"""API."""

import abc
import os
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Type, Union
from urllib.parse import urlencode

import pkg_resources
from rasterio.transform import from_bounds
from rio_tiler.io import BaseReader
from rio_tiler_crs import COGReader

from .. import utils
from ..db.memcache import CacheLayer
from ..dependencies import (
    AssetsParams,
    DefaultDependency,
    ImageParams,
    MetadataParams,
    PathParams,
    PointParams,
    TileParams,
    TMSParams,
    request_hash,
)
from ..models.cog import cogBounds, cogInfo, cogMetadata
from ..models.mapbox import TileJSON
from ..ressources.common import img_endpoint_params
from ..ressources.enums import ImageMimeTypes, ImageType, MimeTypes
from ..ressources.responses import XMLResponse

from fastapi import APIRouter, Depends, Path, Query

from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates

template_dir = pkg_resources.resource_filename("titiler", "templates")
templates = Jinja2Templates(directory=template_dir)


# ref: https://github.com/python/mypy/issues/5374
@dataclass  # type: ignore
class BaseFactory(metaclass=abc.ABCMeta):
    """Tiler Factory."""

    reader: Type[BaseReader] = COGReader
    reader_options: Dict = field(default_factory=dict)

    # FastAPI router
    router: APIRouter = field(default_factory=APIRouter)

    # Endpoint Dependencies
    tms_dependency: Callable = field(default=TMSParams)
    path_dependency: Type[PathParams] = field(default=PathParams)
    tiles_dependency: Type[TileParams] = field(default=TileParams)
    point_dependency: Type[PointParams] = field(default=PointParams)

    # Add `assets` options in endpoint
    add_asset_deps: bool = False

    # Router Prefix is needed to find the path for /tile if the TilerFactory.router is mounted
    # with other router (multiple `.../tile` routes).
    # e.g if you mount the route with `/cog` prefix, set router_prefix to cog and
    # each routes will be prefixed with `cog_`, which will let starlette retrieve routes url (Reverse URL lookups)
    router_prefix: str = ""

    def __post_init__(self):
        """Post Init: register route and configure specific options."""
        self.options = AssetsParams if self.add_asset_deps else DefaultDependency

        if self.router_prefix:
            self.router_prefix = f"{self.router_prefix}_"

        self.register_routes()

    @abc.abstractmethod
    def register_routes(self):
        """Register Tiler Routes."""
        ...


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
        self._info_with_assets() if self.add_asset_deps else self._info()
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
            response_model=cogBounds,
            responses={200: {"description": "Return dataset's bounds."}},
            name=f"{self.router_prefix}bounds",
        )
        def bounds(src_path=Depends(self.path_dependency)):
            """Return the bounds of the COG."""
            reader = src_path.reader or self.reader
            with reader(src_path.url, **self.reader_options) as src_dst:
                return {"bounds": src_dst.bounds}

    ############################################################################
    # /info - with assets
    ############################################################################
    def _info_with_assets(self):
        """Register /info endpoint to router."""

        @self.router.get(
            "/info",
            response_model=Union[List[str], Dict[str, cogInfo]],
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={200: {"description": "Return dataset's basic info."}},
            name=f"{self.router_prefix}info",
        )
        def info(
            src_path=Depends(self.path_dependency), options: AssetsParams = Depends()
        ):
            """Return basic info."""
            reader = src_path.reader or self.reader
            with reader(src_path.url, **self.reader_options) as src_dst:
                if not options.kwargs.get("assets"):
                    return src_dst.assets
                info = src_dst.info(**options.kwargs)
            return info

    ############################################################################
    # /info - without assets
    ############################################################################
    def _info(self):
        """Register /info endpoint to router."""

        @self.router.get(
            "/info",
            response_model=Union[List[str], Dict[str, cogInfo], cogInfo],
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={200: {"description": "Return dataset's basic info."}},
            name=f"{self.router_prefix}info",
        )
        def info(src_path=Depends(self.path_dependency)):
            """Return basic info."""
            reader = src_path.reader or self.reader
            with reader(src_path.url, **self.reader_options) as src_dst:
                info = src_dst.info()
            return info

    ############################################################################
    # /metadata
    ############################################################################
    def _metadata(self):
        """Register /metadata endpoint to router."""

        @self.router.get(
            "/metadata",
            response_model=Union[cogMetadata, Dict[str, cogMetadata]],
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={200: {"description": "Return dataset's metadata."}},
            name=f"{self.router_prefix}metadata",
        )
        def metadata(
            src_path=Depends(self.path_dependency),
            params=Depends(self.metadata_dependency),
            options=Depends(self.options),
        ):
            """Return metadata."""
            reader = src_path.reader or self.reader
            with reader(src_path.url, **self.reader_options) as src_dst:
                info = src_dst.metadata(
                    params.pmin,
                    params.pmax,
                    nodata=params.nodata,
                    indexes=params.indexes,
                    max_size=params.max_size,
                    hist_options=params.hist_options,
                    bounds=params.bounds,
                    resampling_method=params.resampling_method.name,
                    **options.kwargs,
                )
            return info

    ############################################################################
    # /tiles
    ############################################################################
    def _tile(self):  # noqa: C901
        tile_endpoint_params = img_endpoint_params.copy()
        tile_endpoint_params["name"] = f"{self.router_prefix}tile"

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
            options=Depends(self.options),
            cache_client: CacheLayer = Depends(utils.get_cache),
            request_id: str = Depends(request_hash),
        ):
            """Create map tile from a dataset."""
            timings = []
            headers: Dict[str, str] = {}

            tilesize = scale * 256

            content = None
            if cache_client:
                try:
                    content, ext = cache_client.get_image_from_cache(request_id)
                    format = ImageType[ext]
                    headers["X-Cache"] = "HIT"
                except Exception:
                    content = None

            if not content:
                with utils.Timer() as t:
                    reader = src_path.reader or self.reader
                    with reader(
                        src_path.url, tms=tms, **self.reader_options
                    ) as src_dst:
                        tile, mask = src_dst.tile(
                            x,
                            y,
                            z,
                            tilesize=tilesize,
                            indexes=params.indexes,
                            expression=params.expression,
                            nodata=params.nodata,
                            resampling_method=params.resampling_method.name,
                            **options.kwargs,
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

                if cache_client and content:
                    cache_client.set_image_cache(request_id, (content, format.value))

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
            name=f"{self.router_prefix}tilejson",
        )
        @self.router.get(
            "/{TileMatrixSetId}/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
            name=f"{self.router_prefix}tilejson",
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

            q = dict(request.query_params)
            q.pop("TileMatrixSetId", None)
            q.pop("tile_format", None)
            q.pop("tile_scale", None)
            q.pop("minzoom", None)
            q.pop("maxzoom", None)
            qs = urlencode(list(q.items()))

            tiles_url = request.url_for(f"{self.router_prefix}tile", **kwargs)
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

        @self.router.get(
            "/WMTSCapabilities.xml",
            response_class=XMLResponse,
            name=f"{self.router_prefix}wmts",
            tags=["OGC"],
        )
        @self.router.get(
            "/{TileMatrixSetId}/WMTSCapabilities.xml",
            response_class=XMLResponse,
            name=f"{self.router_prefix}wmts",
            tags=["OGC"],
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
            tiles_endpoint = request.url_for(f"{self.router_prefix}tile", **kwargs)
            q = dict(request.query_params)
            q.pop("TileMatrixSetId", None)
            q.pop("tile_format", None)
            q.pop("tile_scale", None)
            q.pop("minzoom", None)
            q.pop("maxzoom", None)
            q.pop("SERVICE", None)
            q.pop("REQUEST", None)
            qs = urlencode(list(q.items()))
            tiles_endpoint += f"?{qs}"

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
                    "tiles_endpoint": tiles_endpoint,
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
            name=f"{self.router_prefix}point",
        )
        def point(
            lon: float = Path(..., description="Longitude"),
            lat: float = Path(..., description="Latitude"),
            src_path=Depends(self.path_dependency),
            params=Depends(self.point_dependency),
            options=Depends(self.options),
        ):
            """Get Point value for a dataset."""
            timings = []
            headers: Dict[str, str] = {}

            with utils.Timer() as t:
                reader = src_path.reader or self.reader
                with reader(src_path.url, **self.reader_options) as src_dst:
                    values = src_dst.point(
                        lon,
                        lat,
                        indexes=params.indexes,
                        expression=params.expression,
                        nodata=params.nodata,
                        **options.kwargs,
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
        prev_endpoint_params["name"] = f"{self.router_prefix}preview"

        @self.router.get(r"/preview", **prev_endpoint_params)
        @self.router.get(r"/preview.{format}", **prev_endpoint_params)
        def preview(
            format: ImageType = Query(
                None, description="Output image type. Default is auto."
            ),
            src_path=Depends(self.path_dependency),
            params=Depends(self.img_dependency),
            options=Depends(self.options),
        ):
            """Create preview of a dataset."""
            timings = []
            headers: Dict[str, str] = {}

            with utils.Timer() as t:
                reader = src_path.reader or self.reader
                with reader(src_path.url, **self.reader_options) as src_dst:
                    data, mask = src_dst.preview(
                        height=params.height,
                        width=params.width,
                        max_size=params.max_size,
                        indexes=params.indexes,
                        expression=params.expression,
                        nodata=params.nodata,
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
        part_endpoint_params["name"] = f"{self.router_prefix}part"

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
            options=Depends(self.options),
        ):
            """Create image from part of a dataset."""
            timings = []
            headers: Dict[str, str] = {}

            with utils.Timer() as t:
                reader = src_path.reader or self.reader
                with reader(src_path.url, **self.reader_options) as src_dst:
                    data, mask = src_dst.part(
                        [minx, miny, maxx, maxy],
                        height=params.height,
                        width=params.width,
                        max_size=params.max_size,
                        indexes=params.indexes,
                        expression=params.expression,
                        nodata=params.nodata,
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
