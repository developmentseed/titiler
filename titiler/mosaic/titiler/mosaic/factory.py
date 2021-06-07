"""TiTiler.mosaic Router factories."""

import os
import uuid
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Type, List
from urllib.parse import urlencode, urlparse

import rasterio
from cogeo_mosaic.backends import BaseBackend, MosaicBackend
from cogeo_mosaic.models import Info as mosaicInfo
from cogeo_mosaic.mosaic import MosaicJSON
from geojson_pydantic.features import Feature
from morecantile import TileMatrixSet
from rio_tiler.constants import MAX_THREADS
from rio_tiler.io import BaseReader, COGReader
from rio_tiler.models import Bounds

from titiler.core.dependencies import WebMercatorTMSParams
from titiler.core.factory import BaseTilerFactory, img_endpoint_params, templates
from titiler.core.models.mapbox import TileJSON
from titiler.core.resources.enums import ImageType, MediaType, OptionalHeader
from titiler.core.resources.responses import GeoJSONResponse, XMLResponse
from titiler.core.utils import Timer, bbox_to_feature
from titiler.mosaic.resources.enums import PixelSelectionMethod
from titiler.mosaic.resources.models import MosaicEntity, UrisRequestBody, StacApiQueryRequestBody, Link, \
    TooManyResultsException, StoreException, UnsupportedOperationException

from fastapi import Depends, Path, Query, Header

from starlette.requests import Request
from starlette.responses import Response

from fastapi import HTTPException
from starlette.status import *
from pystac_client import Client
from asyncio import wait_for
import asyncio
from functools import partial
import traceback
from .settings import mosaic_config
import logging
from cogeo_mosaic.backends import DynamoDBBackend, SQLiteBackend

@dataclass
class MosaicTilerFactory(BaseTilerFactory):
    """
    MosaicTiler Factory.

    The main difference with titiler.endpoint.factory.TilerFactory is that this factory
    needs a reader (MosaicBackend) and a dataset_reader (BaseReader).
    """

    reader: Type[BaseBackend] = MosaicBackend
    dataset_reader: Type[BaseReader] = COGReader

    # BaseBackend does not support other TMS than WebMercator
    tms_dependency: Callable[..., TileMatrixSet] = WebMercatorTMSParams

    backend_options: Dict = field(default_factory=dict)

    def register_routes(self):
        """
        This Method register routes to the router.

        Because we wrap the endpoints in a class we cannot define the routes as
        methods (because of the self argument). The HACK is to define routes inside
        the class method and register them after the class initialisation.

        """

        self.read()
        self.bounds()
        self.info()
        self.tile()
        self.tilejson()
        self.wmts()
        self.point()
        self.validate()
        self.mosaics()

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
        def read(src_path=Depends(self.path_dependency),):
            """Read a MosaicJSON"""
            with self.reader(src_path, **self.backend_options) as mosaic:
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
            with rasterio.Env(**self.gdal_config):
                with self.reader(src_path, **self.backend_options) as src_dst:
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
            with self.reader(src_path, **self.backend_options) as src_dst:
                return src_dst.info()

        @self.router.get(
            "/info.geojson",
            response_model=Feature,
            response_model_exclude_none=True,
            response_class=GeoJSONResponse,
            responses={
                200: {
                    "content": {"application/geo+json": {}},
                    "description": "Return mosaic's basic info as a GeoJSON feature.",
                }
            },
        )
        def info_geojson(
            src_path=Depends(self.path_dependency),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Return mosaic's basic info as a GeoJSON feature."""
            with rasterio.Env(**self.gdal_config):
                with self.reader(src_path, **self.backend_options) as src_dst:
                    info = src_dst.info(**kwargs).dict(exclude_none=True)
                    bounds = info.pop("bounds", None)
                    info.pop("center", None)
                    info["dataset"] = src_path
                    geojson = bbox_to_feature(bounds, properties=info)

            return geojson

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
            colormap=Depends(self.colormap_dependency),
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
            with Timer() as t:
                with rasterio.Env(**self.gdal_config):
                    with self.reader(
                        src_path,
                        reader=self.dataset_reader,
                        reader_options=self.reader_options,
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
                            **layer_params.kwargs,
                            **dataset_params.kwargs,
                            **kwargs,
                        )
            timings.append(("dataread", round((t.elapsed - mosaic_read) * 1000, 2)))

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
                    colormap=colormap,
                    **format.profile,
                    **render_params.kwargs,
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
            render_params=Depends(self.render_dependency),  # noqa
            colormap=Depends(self.colormap_dependency),  # noqa
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

            with self.reader(src_path, **self.backend_options) as src_dst:
                center = list(src_dst.center)
                if minzoom:
                    center[-1] = minzoom
                return {
                    "bounds": src_dst.bounds,
                    "center": tuple(center),
                    "minzoom": minzoom if minzoom is not None else src_dst.minzoom,
                    "maxzoom": maxzoom if maxzoom is not None else src_dst.maxzoom,
                    "name": urlparse(src_path).path.lstrip("/") or "mosaic",
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
            render_params=Depends(self.render_dependency),  # noqa
            colormap=Depends(self.colormap_dependency),  # noqa
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

            with self.reader(src_path, **self.backend_options) as src_dst:
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

            with Timer() as t:
                with rasterio.Env(**self.gdal_config):
                    with self.reader(
                        src_path,
                        reader=self.dataset_reader,
                        reader_options=self.reader_options,
                        **self.backend_options,
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

    ############################################################################
    # /mosaics
    ############################################################################
    def mosaics(self):  # noqa: C901
        """Register /mosaics endpoints."""

        # with dynamodb backend, the tiles field for this is always empty
        # https://github.com/developmentseed/cogeo-mosaic/issues/175
        @self.router.get(
            "/mosaics/{mosaic_id}",
            response_model=MosaicEntity,
            responses={
                HTTP_200_OK: {"description": "Return a Mosaic resource for the given ID."},
                HTTP_404_NOT_FOUND: {"description": "Mosaic resource for the given ID does not exist."},
            },
        )
        async def get_mosaic(
                request: Request,
                mosaic_id: str
        ) -> MosaicEntity:
            self_uri = request.url_for("get_mosaic", mosaic_id=mosaic_id)
            if await retrieve(mosaic_id):
                return mk_mosaic_entity(mosaic_id=mosaic_id, self_uri=self_uri)
            else:
                raise HTTPException(HTTP_404_NOT_FOUND, f"Error: mosaic with given ID does not exist.")

        @self.router.get(
            "/mosaics/{mosaic_id}/mosaicjson",
            response_model=MosaicJSON,
            responses={
                200: {"description": "Return a MosaicJSON definition for the given ID."},
                404: {"description": "Mosaic resource for the given ID does not exist."},
            },
        )
        async def get_mosaic_mosaicjson(mosaic_id: str) -> MosaicJSON:
            if m := await retrieve(mosaic_id, include_tiles=True):
                return m
            else:
                raise HTTPException(HTTP_404_NOT_FOUND, f"Error: mosaic with given ID does not exist.")

        # derived from cogeo.xyz
        @self.router.get(
            r"/mosaics/{mosaic_id}/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson for the given ID."},
                       404: {"description": "Mosaic resource for the given ID does not exist."},
                       },
            response_model_exclude_none=True,
        )
        async def get_mosaic_tilejson(
                mosaic_id: str,
                request: Request,
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
        ) -> TileJSON:
            """Return TileJSON document for a MosaicJSON."""

            kwargs = {
                "mosaic_id": mosaic_id,
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
                "scale": tile_scale,
            }
            if tile_format:
                kwargs["format"] = tile_format.value
            tiles_url = request.url_for("tile", **kwargs)

            q = dict(request.query_params)
            q.pop("TileMatrixSetId", None)
            q.pop("tile_format", None)
            q.pop("tile_scale", None)
            qs = urlencode(list(q.items()))
            tiles_url += f"?{qs}"



            if mosaicjson := await retrieve(mosaic_id):
                center = list(mosaicjson.center)
                if minzoom:
                    center[-1] = minzoom
                return TileJSON(
                    bounds=mosaicjson.bounds,
                    center=tuple(center),
                    minzoom=minzoom if minzoom is not None else mosaicjson.minzoom,
                    maxzoom=maxzoom if maxzoom is not None else mosaicjson.maxzoom,
                    name=mosaic_id,
                    tiles=[tiles_url],
                )
            else:
                raise HTTPException(HTTP_404_NOT_FOUND, f"Error: mosaic with given ID does not exist.")

        @self.router.post(
            "/mosaics",
            status_code=HTTP_201_CREATED,
            responses={
                HTTP_201_CREATED: {"description": "Created a new mosaic"},
                HTTP_409_CONFLICT: {"description": "Conflict while trying to create mosaic"},
                HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Mosaic could not be created"}
            },
            response_model=MosaicEntity,
        )
        async def post_mosaics(
                request: Request,
                response: Response,
                content_type: Optional[str] = Header(None)
        ) -> MosaicEntity:
            """Create a MosaicJSON"""

            mosaicjson = await populate_mosaicjson(request, content_type)
            mosaic_id = str(uuid.uuid4())

            # this probably can't happen, but just to be safe...
            try:
                await store(mosaic_id, mosaicjson, overwrite=False)
            except StoreException as e:
                raise HTTPException(HTTP_409_CONFLICT, f"Error: mosaic with given ID already exists")
            except Exception as e:
                raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, f"Error: could not save mosaic")

            self_uri = request.url_for("get_mosaic", mosaic_id=mosaic_id)

            response.headers["Location"] = self_uri

            return mk_mosaic_entity(mosaic_id, self_uri, mosaicjson)

        @self.router.put(
            "/mosaics/{mosaic_id}",
            status_code=HTTP_204_NO_CONTENT,
            responses={
                HTTP_204_NO_CONTENT : {"description": "Updated a mosaic"},
                HTTP_404_NOT_FOUND: {"description": "Mosaic with ID not found"},
                HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Mosaic could not be updated"}
            }
        )
        async def put_mosaic(
                mosaic_id: str,
                request: Request,
                content_type: Optional[str] = Header(None),
        ) -> None:
            """Update an existing MosaicJSON"""

            mosaicjson = await populate_mosaicjson(request, content_type)

            try:
                await store(mosaic_id, mosaicjson, overwrite=True)
            except StoreException as e:
                raise HTTPException(HTTP_404_NOT_FOUND, f"Error: mosaic with given ID does not exist.")
            except Exception as e:
                raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, f"Error: could not update mosaic.")

            return

        # note: cogeo-mosaic doesn't clear the cache on write/delete, so these will stay until the TTL expires
        # https://github.com/developmentseed/cogeo-mosaic/issues/176
        @self.router.delete(
            "/mosaics/{mosaic_id}",
            status_code=HTTP_204_NO_CONTENT,
        )
        async def delete_mosaic(
                mosaic_id: str,
                request: Request
        ) -> None:
            """Delete an existing MosaicJSON"""

            try:
                await retrieve(mosaic_id)
            except Exception as e:
                raise HTTPException(HTTP_404_NOT_FOUND, f"Error: mosaic with given ID does not exist.")

            try:
                await delete(mosaic_id)
            except UnsupportedOperationException:
                raise HTTPException(HTTP_405_METHOD_NOT_ALLOWED,
                                    f"Error: mosaic with given ID cannot be deleted because the datastore does not support it.")


        # copied from cogeo-xyz
        # todo: async
        @self.router.get(r"/mosaics/{mosaic_id}/tiles/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(r"/mosaics/{mosaic_id}/tiles/{z}/{x}/{y}.{format}", **img_endpoint_params)
        @self.router.get(r"/mosaics/{mosaic_id}/tiles/{z}/{x}/{y}@{scale}x", **img_endpoint_params)
        @self.router.get(
            r"/mosaics/{mosaic_id}/tiles/{z}/{x}/{y}@{scale}x.{format}", **img_endpoint_params
        )
        def tile(
                mosaic_id: str,
                z: int = Path(..., ge=0, le=30, description="Mercator tiles's zoom level"),
                x: int = Path(..., description="Mercator tiles's column"),
                y: int = Path(..., description="Mercator tiles's row"),
                scale: int = Query(
                    1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
                ),
                format: ImageType = Query(
                    None, description="Output image type. Default is auto."
                ),
                layer_params=Depends(self.layer_dependency),
                dataset_params=Depends(self.dataset_dependency),
                render_params=Depends(self.render_dependency),
                colormap=Depends(self.colormap_dependency),
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
            with Timer() as t:
                mosaic_uri = mk_src_path(mosaic_id)

                with rasterio.Env(**self.gdal_config):
                    with self.reader(
                            mosaic_uri,
                            reader=self.dataset_reader,
                            reader_options=self.reader_options,
                            **self.backend_options,
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
                    colormap=colormap,
                    **format.profile,
                    **render_params.kwargs,
                )
            timings.append(("format", round(t.elapsed * 1000, 2)))

            if OptionalHeader.server_timing in self.optional_headers:
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            if OptionalHeader.x_assets in self.optional_headers:
                headers["X-Assets"] = ",".join(data.assets)

            return Response(content, media_type=format.mediatype, headers=headers)

        # auxiliary methods

        async def mosaicjson_from_urls(urisrb: UrisRequestBody) -> MosaicJSON:

            if len(urisrb.urls) > MAX_ITEMS:
                raise HTTPException(HTTP_400_BAD_REQUEST, f"Error: a maximum of {MAX_ITEMS} URLs can be mosaiced.")

            loop = asyncio.get_running_loop()

            try:
                mosaicjson = await wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: MosaicJSON.from_urls(
                            urls=urisrb.urls,
                            minzoom=urisrb.minzoom,
                            maxzoom=urisrb.maxzoom,
                            max_threads=int(os.getenv("MOSAIC_CONCURRENCY", MAX_THREADS)),  # todo
                        ),
                    ),
                    20
                )
            except asyncio.TimeoutError:
                raise HTTPException(
                    HTTP_500_INTERNAL_SERVER_ERROR,
                    f"Error: timeout reading URLs and generating MosaicJSON definition"
                )

            if mosaicjson is None:
                raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, f"Error: could not extract mosaic data")

            mosaicjson.name = urisrb.name
            mosaicjson.description = urisrb.description
            mosaicjson.attribution = urisrb.attribution
            mosaicjson.version = urisrb if urisrb.version else "0.0.1"

            return mosaicjson

        async def mosaicjson_from_stac_api_query(req: StacApiQueryRequestBody) -> MosaicJSON:
            """Create a mosaic for the given parameters"""

            if not req.stac_api_root:
                raise HTTPException(HTTP_400_BAD_REQUEST, f"Error: stac_api_root field must be non-empty.")

            loop = asyncio.get_running_loop()

            try:
                try:
                    features = await wait_for(
                        loop.run_in_executor(None, execute_stac_search, req),
                        30
                    )
                except asyncio.TimeoutError:
                    raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, "Error: timeout executing STAC API search.")
                except TooManyResultsException as e:
                    raise HTTPException(HTTP_400_BAD_REQUEST, f"Error: too many results from STAC API Search: {e}")

                if not features:
                    raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, "Error: STAC API Search returned no results.")

                try:
                    mosaicjson = await wait_for(
                        loop.run_in_executor(
                            None,
                            extract_mosaicjson_from_features,
                            features,
                            req.asset_name if req.asset_name else "visual"),
                        60 # todo: how much time should/can it take?
                    )
                except asyncio.TimeoutError:
                    raise HTTPException(
                        HTTP_500_INTERNAL_SERVER_ERROR,
                        f"Error: timeout reading a COG asset and generating MosaicJSON definition"
                    )

                if mosaicjson is None:
                    raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, f"Error: could not extract mosaic data")

                mosaicjson.name = req.name
                mosaicjson.description = req.description
                mosaicjson.attribution = req.attribution
                mosaicjson.version = req if req.version else "0.0.1"

                return mosaicjson

            except HTTPException as e:
                raise e
            except Exception as e:
                raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, f"Error: {e}")

        MAX_ITEMS=100

        def execute_stac_search(mosaic_request: StacApiQueryRequestBody) -> List[dict]:
            try:
                search_result = Client.open(mosaic_request.stac_api_root).search(
                    ## **mosaic_request.dict(), ?? this feel a little unsafe
                    ids=mosaic_request.ids,
                    collections=mosaic_request.collections,
                    datetime=mosaic_request.datetime,
                    bbox=mosaic_request.bbox,
                    intersects=mosaic_request.intersects,
                    query=mosaic_request.query,
                    max_items=MAX_ITEMS,
                    limit=mosaic_request.limit if mosaic_request.limit else 100,
                    # setting limit >500 causes an error https://github.com/stac-utils/pystac-client/issues/56
                )
                matched = search_result.matched()
                if matched > MAX_ITEMS:
                    raise TooManyResultsException(
                        f"too many results: {matched} Items matched, but only a maximum of {MAX_ITEMS} are allowed.")

                return search_result.items_as_collection().to_dict()['features']
            except TooManyResultsException as e:
                raise e
            except Exception as e:
                raise Exception(f"STAC Search error: {e}")

        # assumes all assets are uniform. get the min and max zoom from the first.
        def extract_mosaicjson_from_features(features: List[dict], asset_name: str) -> Optional[MosaicJSON]:
            if features:
                try:
                    with COGReader(asset_href(features[0], asset_name)) as cog:
                        info = cog.info()
                    return MosaicJSON.from_features(
                        features,
                        minzoom=info.minzoom,
                        maxzoom=info.maxzoom,
                        accessor=partial(asset_href, asset_name=asset_name)
                    )

                # when Item geometry is a MultiPolygon (instead of a Polygon), supermercado raises
                # handle error "local variable 'x' referenced before assignment"
                # supermercado/burntiles.py ", line 38, in _feature_extrema
                # as this method only handles Polygon, LineString, and Point :grimace:
                # https://github.com/mapbox/supermercado/issues/47
                except UnboundLocalError:
                    traceback.print_exc()
                    raise Exception(f"STAC Items likely have MultiPolygon geometry, and only Polygon is supported.")
                except Exception as e:
                    raise Exception(f"Error extracting mosaic data from results: {e}")
            else:
                return None

        # todo: make this safer in case visual doesn't exist
        # how to handle others?
        # support for selection by role?
        def asset_href(feature: dict, asset_name: str) -> str:
            if href := feature.get("assets", {}).get(asset_name, {}).get("href"):
                return href
            else:
                raise Exception(f"Asset with name '{asset_name}' could not be found.")

        def mk_src_path(mosaic_id: str) -> str:
            if mosaic_config.backend == "dynamodb://":
                return f"{mosaic_config.backend}{mosaic_config.host}:{mosaic_id}"
            else:
                return f"{mosaic_config.backend}{mosaic_config.host}/{mosaic_id}{mosaic_config.format}"

        async def store(mosaic_id: str, mosaicjson: MosaicJSON, overwrite: bool) -> None:
            try:
                await retrieve(mosaic_id)
            except Exception as e:
                existing = False
            else:
                existing = True

            if not overwrite and existing:
                raise StoreException("Attempting to create already existing mosaic")
            if overwrite and not existing:
                raise StoreException("Attempting to update non-existant mosaic")

            mosaic_uri = mk_src_path(mosaic_id)
            loop = asyncio.get_running_loop()

            try:
                await wait_for(
                    loop.run_in_executor(None, mosaic_write, mosaic_uri, mosaicjson, overwrite),
                    20
                )
            except asyncio.TimeoutError:
                raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, "Error: timeout storing mosaic in datastore")

        def mosaic_write(mosaic_uri: str, mosaicjson: MosaicJSON, overwrite: bool) -> None:
            with rasterio.Env(**self.gdal_config):
                with self.reader(mosaic_uri, mosaic_def=mosaicjson) as mosaic:
                    mosaic.write(overwrite=overwrite)

        async def retrieve(mosaic_id: str, include_tiles: bool = False) -> MosaicJSON:
            mosaic_uri = mk_src_path(mosaic_id)
            loop = asyncio.get_running_loop()

            try:
                mosaicjson = await wait_for(
                    loop.run_in_executor(None, read_mosaicjson_sync, mosaic_uri, include_tiles),
                    20
                )
            except asyncio.TimeoutError:
                raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, "Error: timeout retrieving mosaic from datastore.")

            return mosaicjson

        def read_mosaicjson_sync(mosaic_uri: str, include_tiles: bool) -> MosaicJSON:
            with rasterio.Env(**self.gdal_config):
                with self.reader(mosaic_uri,
                                 reader=self.dataset_reader,
                                 reader_options=self.reader_options,
                                 **self.backend_options) as mosaic:
                    mosaicjson = mosaic.mosaic_def
                    if include_tiles and isinstance(mosaic, DynamoDBBackend):
                        keys = (mosaic._fetch_dynamodb(qk) for qk in mosaic._quadkeys)
                        mosaicjson.tiles = {x["quadkey"]: x["assets"] for x in keys}
                    return mosaicjson


        async def delete(mosaic_id: str) -> None:
            mosaic_uri = mk_src_path(mosaic_id)
            loop = asyncio.get_running_loop()

            try:
                mosaicjson = await wait_for(
                    loop.run_in_executor(None, delete_mosaicjson_sync, mosaic_uri),
                    20
                )
            except asyncio.TimeoutError:
                raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, "Error: timeout deleting mosaic.")

            return mosaicjson

        def delete_mosaicjson_sync(mosaic_uri: str) -> None:
                with rasterio.Env(**self.gdal_config):
                    with self.reader(mosaic_uri,
                                     reader=self.dataset_reader,
                                     reader_options=self.reader_options,
                                     **self.backend_options) as mosaic:
                        if isinstance(mosaic, DynamoDBBackend):
                            mosaic.delete() # delete is only supported by DynamoDB
                        else:
                            raise UnsupportedOperationException("Delete is not supported")


        def mk_base_uri(request: Request):
            return f"{request.url.scheme}://{request.headers['host']}"

        def mk_mosaic_entity(mosaic_id, self_uri, mosaicjson: Optional[MosaicJSON] = None):
            return MosaicEntity(
                id=mosaic_id,
                links=[
                    Link(
                        rel="self",
                        href=self_uri,
                        type="application/json",
                        title="Self"
                    ),
                    Link(
                        rel="mosaicjson",
                        href=f"{self_uri}/mosaicjson",
                        type="application/vnd.titiler.mosaicjson+json",
                        title="MosiacJSON"
                    ),
                    Link(
                        rel="tilejson",
                        href=f"{self_uri}/tilejson.json",
                        type="application/json",
                        title="TileJSON"
                    ),
                    Link(
                        rel="tiles",
                        href=f"{self_uri}/tiles/{{z}}/{{x}}/{{y}}",
                        type="application/json",
                        title="Tiles Endpoint"
                    )
                ])

        async def populate_mosaicjson(request, content_type):
            body_json = await request.json()
            if not content_type or \
                    content_type == "application/json" or \
                    content_type == "application/json; charset=utf-8" or \
                    content_type == "application/vnd.titiler.mosaicjson+json":
                mosaicjson = MosaicJSON(**body_json)
            elif content_type == "application/vnd.titiler.urls+json":
                mosaicjson = await mosaicjson_from_urls(UrisRequestBody(**body_json))
            elif content_type == "application/vnd.titiler.stac-api-query+json":
                mosaicjson = await mosaicjson_from_stac_api_query(StacApiQueryRequestBody(**body_json))
            else:
                raise HTTPException(
                    HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    "Error: media in Content-Type header is not supported."
                )
            return mosaicjson
