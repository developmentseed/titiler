"""TiTiler.mosaic Router factories."""

import os
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Type, Union
from urllib.parse import urlencode

import rasterio
from cogeo_mosaic.backends import BaseBackend, MosaicBackend
from cogeo_mosaic.models import Info as mosaicInfo
from cogeo_mosaic.mosaic import MosaicJSON
from geojson_pydantic.features import Feature
from geojson_pydantic.geometries import Polygon
from morecantile import TileMatrixSet
from rio_tiler.constants import MAX_THREADS
from rio_tiler.io import BaseReader, COGReader, MultiBandReader, MultiBaseReader
from rio_tiler.models import Bounds

from titiler.core.dependencies import WebMercatorTMSParams
from titiler.core.factory import BaseTilerFactory, img_endpoint_params, templates
from titiler.core.models.mapbox import TileJSON
from titiler.core.resources.enums import ImageType, MediaType, OptionalHeader
from titiler.core.resources.responses import GeoJSONResponse, JSONResponse, XMLResponse
from titiler.core.utils import Timer
from titiler.mosaic.models.responses import Point
from titiler.mosaic.resources.enums import PixelSelectionMethod

from fastapi import Depends, Path, Query

from starlette.requests import Request
from starlette.responses import Response


@dataclass
class MosaicTilerFactory(BaseTilerFactory):
    """
    MosaicTiler Factory.

    The main difference with titiler.endpoint.factory.TilerFactory is that this factory
    needs the `reader` to be of `cogeo_mosaic.backends.BaseBackend` type (e.g MosaicBackend) and a `dataset_reader` (BaseReader).
    """

    reader: Type[BaseBackend] = MosaicBackend
    dataset_reader: Union[
        Type[BaseReader],
        Type[MultiBaseReader],
        Type[MultiBandReader],
    ] = COGReader

    # BaseBackend does not support other TMS than WebMercator
    tms_dependency: Callable[..., TileMatrixSet] = WebMercatorTMSParams

    backend_options: Dict = field(default_factory=dict)

    def register_routes(self):
        """
        This Method register routes to the router.

        Because we wrap the endpoints in a class we cannot define the routes as
        methods (because of the self argument). The HACK is to define routes inside
        the class method and register them after the class initialization.

        """

        self.read()
        self.bounds()
        self.info()
        self.tile()
        self.tilejson()
        self.wmts()
        self.point()
        self.validate()
        self.assets()

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
            deprecated=True,
        )
        @self.router.get(
            "/",
            response_model=MosaicJSON,
            response_model_exclude_none=True,
            responses={200: {"description": "Return MosaicJSON definition"}},
        )
        def read(src_path=Depends(self.path_dependency)):
            """Read a MosaicJSON"""
            with rasterio.Env(**self.gdal_config):
                with self.reader(
                    src_path,
                    reader=self.dataset_reader,
                    **self.backend_options,
                ) as src_dst:
                    return src_dst.mosaic_def

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
            with rasterio.Env(**self.gdal_config):
                with self.reader(
                    src_path,
                    reader=self.dataset_reader,
                    **self.backend_options,
                ) as src_dst:
                    return {"bounds": src_dst.geographic_bounds}

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
            with rasterio.Env(**self.gdal_config):
                with self.reader(
                    src_path,
                    reader=self.dataset_reader,
                    **self.backend_options,
                ) as src_dst:
                    return src_dst.info()

        @self.router.get(
            "/info.geojson",
            response_model=Feature[Polygon, mosaicInfo],
            response_model_exclude_none=True,
            response_class=GeoJSONResponse,
            responses={
                200: {
                    "content": {"application/geo+json": {}},
                    "description": "Return mosaic's basic info as a GeoJSON feature.",
                }
            },
        )
        def info_geojson(src_path=Depends(self.path_dependency)):
            """Return mosaic's basic info as a GeoJSON feature."""
            with rasterio.Env(**self.gdal_config):
                with self.reader(
                    src_path,
                    reader=self.dataset_reader,
                    **self.backend_options,
                ) as src_dst:
                    info = src_dst.info()
                    return Feature(
                        geometry=Polygon.from_bounds(*info.bounds), properties=info
                    )

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
            pixel_selection: PixelSelectionMethod = Query(
                PixelSelectionMethod.first, description="Pixel selection method."
            ),
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
        ):
            """Create map tile from a COG."""
            timings = []
            headers: Dict[str, str] = {}

            tilesize = scale * 256

            threads = int(os.getenv("MOSAIC_CONCURRENCY", MAX_THREADS))
            with Timer() as t:
                with rasterio.Env(**self.gdal_config):
                    with self.reader(
                        src_path,
                        reader=self.dataset_reader,
                        **self.backend_options,
                    ) as src_dst:
                        mosaic_read = t.from_start
                        timings.append(("mosaicread", round(mosaic_read * 1000, 2)))

                        data, _ = src_dst.tile(
                            x,
                            y,
                            z,
                            pixel_selection=pixel_selection.method(),
                            tilesize=tilesize,
                            threads=threads,
                            tile_buffer=tile_buffer,
                            **layer_params,
                            **dataset_params,
                        )
            timings.append(("dataread", round((t.elapsed - mosaic_read) * 1000, 2)))

            if not format:
                format = ImageType.jpeg if data.mask.all() else ImageType.png

            with Timer() as t:
                image = data.post_process(**postprocess_params)
            timings.append(("postprocess", round(t.elapsed * 1000, 2)))

            with Timer() as t:
                content = image.render(
                    img_format=format.driver,
                    colormap=colormap,
                    **format.profile,
                    **render_params,
                )
            timings.append(("format", round(t.elapsed * 1000, 2)))

            if OptionalHeader.server_timing in self.optional_headers:
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            if OptionalHeader.x_assets in self.optional_headers:
                headers["X-Assets"] = ",".join(data.assets)

            return Response(content, media_type=format.mediatype, headers=headers)

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
            pixel_selection: PixelSelectionMethod = Query(
                PixelSelectionMethod.first, description="Pixel selection method."
            ),  # noqa
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
                with self.reader(
                    src_path,
                    reader=self.dataset_reader,
                    **self.backend_options,
                ) as src_dst:
                    center = list(src_dst.mosaic_def.center)
                    if minzoom is not None:
                        center[-1] = minzoom
                    return {
                        "bounds": src_dst.bounds,
                        "center": tuple(center),
                        "minzoom": minzoom if minzoom is not None else src_dst.minzoom,
                        "maxzoom": maxzoom if maxzoom is not None else src_dst.maxzoom,
                        "tiles": [tiles_url],
                    }

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
            pixel_selection: PixelSelectionMethod = Query(
                PixelSelectionMethod.first, description="Pixel selection method."
            ),  # noqa
            postprocess_params=Depends(self.process_dependency),  # noqa
            colormap=Depends(self.colormap_dependency),  # noqa
            render_params=Depends(self.render_dependency),  # noqa
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
                with self.reader(
                    src_path,
                    reader=self.dataset_reader,
                    **self.backend_options,
                ) as src_dst:
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
                    "title": "Mosaic",
                    "layer_name": "mosaic",
                    "media_type": tile_format.mediatype,
                },
                media_type=MediaType.xml.value,
            )

    ############################################################################
    # /point (Optional)
    ############################################################################
    def point(self):
        """Register /point endpoint."""

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
        ):
            """Get Point value for a Mosaic."""
            timings = []
            threads = int(os.getenv("MOSAIC_CONCURRENCY", MAX_THREADS))

            with Timer() as t:
                with rasterio.Env(**self.gdal_config):
                    with self.reader(
                        src_path,
                        reader=self.dataset_reader,
                        **self.backend_options,
                    ) as src_dst:
                        mosaic_read = t.from_start
                        timings.append(("mosaicread", round(mosaic_read * 1000, 2)))
                        values = src_dst.point(
                            lon,
                            lat,
                            threads=threads,
                            **layer_params,
                            **dataset_params,
                        )
            timings.append(("dataread", round((t.elapsed - mosaic_read) * 1000, 2)))

            if OptionalHeader.server_timing in self.optional_headers:
                response.headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            return {"coordinates": [lon, lat], "values": values}

    def validate(self):
        """Register /validate endpoint."""

        @self.router.post("/validate")
        def validate(body: MosaicJSON):
            """Validate a MosaicJSON"""
            return True

    def assets(self):
        """Register /assets endpoint."""

        @self.router.get(
            r"/{minx},{miny},{maxx},{maxy}/assets",
            responses={200: {"description": "Return list of COGs in bounding box"}},
        )
        def assets_for_bbox(
            src_path=Depends(self.path_dependency),
            minx: float = Query(None, description="Left side of bounding box"),
            miny: float = Query(None, description="Bottom of bounding box"),
            maxx: float = Query(None, description="Right side of bounding box"),
            maxy: float = Query(None, description="Top of bounding box"),
        ):
            """Return a list of assets which overlap a bounding box"""
            with rasterio.Env(**self.gdal_config):
                with self.reader(
                    src_path,
                    reader=self.dataset_reader,
                    **self.backend_options,
                ) as src_dst:
                    return src_dst.assets_for_bbox(minx, miny, maxx, maxy)

        @self.router.get(
            r"/{lng},{lat}/assets",
            responses={200: {"description": "Return list of COGs"}},
        )
        def assets_for_lon_lat(
            src_path=Depends(self.path_dependency),
            lng: float = Query(None, description="Longitude"),
            lat: float = Query(None, description="Latitude"),
        ):
            """Return a list of assets which overlap a point"""
            with rasterio.Env(**self.gdal_config):
                with self.reader(
                    src_path,
                    reader=self.dataset_reader,
                    **self.backend_options,
                ) as src_dst:
                    return src_dst.assets_for_point(lng, lat)

        @self.router.get(
            r"/{z}/{x}/{y}/assets",
            responses={200: {"description": "Return list of COGs"}},
        )
        def assets_for_tile(
            z: int = Path(..., ge=0, le=30, description="Mercator tiles's zoom level"),
            x: int = Path(..., description="Mercator tiles's column"),
            y: int = Path(..., description="Mercator tiles's row"),
            src_path=Depends(self.path_dependency),
        ):
            """Return a list of assets which overlap a given tile"""
            with rasterio.Env(**self.gdal_config):
                with self.reader(
                    src_path,
                    reader=self.dataset_reader,
                    **self.backend_options,
                ) as src_dst:
                    return src_dst.assets_for_tile(x, y, z)
