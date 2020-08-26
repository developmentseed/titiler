"""API."""

import os
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional
from urllib.parse import urlencode

import pkg_resources
from cogeo_mosaic.backends import BaseBackend, MosaicBackend
from cogeo_mosaic.mosaic import MosaicJSON
from cogeo_mosaic.utils import get_footprints
from rasterio.transform import from_bounds
from rio_tiler.constants import MAX_THREADS
from rio_tiler.io import BaseReader
from rio_tiler_crs import COGReader

from .. import utils
from ..db.memcache import CacheLayer
from ..dependencies import MosaicTMSParams, request_hash
from ..errors import BadRequestError, TileNotFoundError
from ..models.cog import cogBounds
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
from .factory import BaseFactory

from fastapi import Depends, Path, Query

from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates

template_dir = pkg_resources.resource_filename("titiler", "templates")
templates = Jinja2Templates(directory=template_dir)


@dataclass
class MosaicTilerFactory(BaseFactory):
    """
    MosaicTiler Factory.

    The main difference with titiler.endpoint.factory.TilerFactory is that this factory
    needs a reader (MosaicBackend) and a dataset_reader (BaseReader).
    """

    reader: BaseBackend = field(default=MosaicBackend)
    dataset_reader: BaseReader = field(default=COGReader)

    tms_dependency: Callable = field(default=MosaicTMSParams)

    add_asset_deps: bool = True  # We add if by default

    def __post_init__(self):
        """Post Init: inherit post init from the Parent class."""
        super().__post_init__()

    def register_routes(self):
        """
        This Method register routes to the router.

        Because we wrap the endpoints in a class we cannot define the routes as
        methods (because of the self argument). The HACK is to define routes inside
        the class method and register them after the class initialisation.

        """

        self._read()
        self._create()
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
            name=f"{self.router_prefix}read",
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
            "",
            response_model=MosaicJSON,
            response_model_exclude_none=True,
            name=f"{self.router_prefix}create",
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
            "",
            response_model=MosaicJSON,
            response_model_exclude_none=True,
            name=f"{self.router_prefix}update",
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
            response_model=cogBounds,
            responses={200: {"description": "Return the bounds of the MosaicJSON"}},
            name=f"{self.router_prefix}bounds",
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
            name=f"{self.router_prefix}info",
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
            pixel_selection: PixelSelectionMethod = Query(
                PixelSelectionMethod.first, description="Pixel selection method."
            ),
            cache_client: CacheLayer = Depends(utils.get_cache),
            request_id: str = Depends(request_hash),
        ):
            """Create map tile from a COG."""
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
                    reader = src_path.reader or self.dataset_reader
                    reader_options = {**self.reader_options, "tms": tms}

                    threads = int(os.getenv("MOSAIC_CONCURRENCY", MAX_THREADS))

                    with self.reader(
                        src_path.url, reader=reader, reader_options=reader_options
                    ) as src_dst:
                        (data, mask), assets_used = src_dst.tile(
                            x,
                            y,
                            z,
                            pixel_selection=pixel_selection.method(),
                            threads=threads,
                            tilesize=tilesize,
                            indexes=params.indexes,
                            expression=params.expression,
                            nodata=params.nodata,
                            resampling_method=params.resampling_method.name,
                            **options.kwargs,
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

                if cache_client and content:
                    cache_client.set_image_cache(request_id, (content, format.value))

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

            q = dict(request.query_params)
            q.pop("TileMatrixSetId", None)
            q.pop("tile_format", None)
            q.pop("tile_scale", None)
            q.pop("minzoom", None)
            q.pop("maxzoom", None)
            qs = urlencode(list(q.items()))

            tiles_url = request.url_for(f"{self.router_prefix}tile", **kwargs)
            tiles_url += f"?{qs}"

            with self.reader(src_path.url,) as src_dst:
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
        )
        @self.router.get(
            "/{TileMatrixSetId}/WMTSCapabilities.xml",
            response_class=XMLResponse,
            name=f"{self.router_prefix}wmts",
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
    # /point (Optional)
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
            """Get Point value for a Mosaic."""
            timings = []
            headers: Dict[str, str] = {}
            threads = int(os.getenv("MOSAIC_CONCURRENCY", MAX_THREADS))

            with utils.Timer() as t:
                reader = src_path.reader or self.dataset_reader
                with self.reader(
                    src_path.url, reader=reader, reader_options=self.reader_options,
                ) as src_dst:
                    values = src_dst.point(
                        lon,
                        lat,
                        threads=threads,
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
