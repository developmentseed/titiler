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
from titiler.mosaic.resources.models import MosaicEntity, UrisRequestBody, StacApiQueryRequestBody, Link

from fastapi import Depends, Path, Query, Header

from starlette.requests import Request
from starlette.responses import Response

from fastapi import HTTPException
from starlette.status import *
from pystac_client import Client
from asyncio import wait_for
import asyncio
from functools import partial
from collections import defaultdict

# TODO: remove!!!!
mj_store: Dict[str, MosaicJSON] = {}


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

        @self.router.get(r"/mosaics/{mosaic_id}")
        def get_mosaic(
                request: Request,
                mosaic_id: str
        ) -> MosaicEntity:
            base_uri = f"{request.url.scheme}://{request.headers['host']}"
            self_uri = f"{base_uri}/mosaicjson/mosaics/{mosaic_id}"
            return mk_mosaic_entity(mosaic_id=mosaic_id, self_uri=self_uri, base_uri=base_uri)

        @self.router.get(r"/mosaics/{mosaic_id}/mosaicjson")
        def get_mosaic_mosaicjson(mosaic_id: str) -> MosaicJSON:
            return retrieve(mosaic_id)

        @self.router.post("/mosaics")
        async def post_mosaics(
                request: Request,
                response: Response,
                content_type: Optional[str] = Header(None),
        ) -> MosaicEntity:
            """Validate a MosaicJSON"""

            body_json = await request.json()
            if not content_type or \
                    content_type == "application/json" or \
                    content_type == "application/json; charset=utf-8" or \
                    content_type == "application/vnd.titiler.mosaicjson+json":
                mosaicjson = MosaicJSON(**body_json)
            elif content_type == "application/vnd.titiler.urls+json":
                mosaicjson = mosaicjson_from_urls(UrisRequestBody(**body_json))
            elif content_type == "application/vnd.titiler.stac-api-query+json":
                mosaicjson = await mosaicjson_from_stac_api_query(StacApiQueryRequestBody(**body_json))
            else:
                raise HTTPException(
                    HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                                    "Error: media in Content-Type header is not supported."
                                    )

            # todo: validate mosaicjson ??

            mj_id = str(uuid.uuid4())

            store(mj_id, mosaicjson)

            base_uri = f"{request.url.scheme}://{request.headers['host']}"
            self_uri = f"{base_uri}/mosaicjson/mosaics/{mj_id}"

            response.headers["Location"] = self_uri

            return mk_mosaic_entity(mj_id, self_uri, base_uri, mosaicjson)

        @self.router.put("/mosaics/{id}")
        def put_mosaics(
                id: str,
                request: Request,
                content_type: Optional[str] = Header(None),
        ):
            """Update an existing MosaicJSON"""
            return None

        # todo: async this
        def mosaicjson_from_urls(urirb: UrisRequestBody) -> MosaicJSON:
            mosaicjson = MosaicJSON.from_urls(
                urls=urirb.urls,
                minzoom=urirb.minzoom,
                maxzoom=urirb.maxzoom,
                max_threads=int(os.getenv("MOSAIC_CONCURRENCY", MAX_THREADS)),  # todo
            )
            mosaicjson.name = urirb.name
            mosaicjson.description = urirb.description
            mosaicjson.attribution = urirb.attribution
            return mosaicjson

        async def mosaicjson_from_stac_api_query(req: StacApiQueryRequestBody) -> MosaicJSON:
            """Create a mosaic for the given parameters"""

            if not req.stac_api_root:
                raise HTTPException(HTTP_400_BAD_REQUEST, f"Error: stac_api_root field must be non-empty.")

            loop = asyncio.get_running_loop()

            try:
                try:
                    features = await wait_for(
                        loop.run_in_executor( None, execute_stac_search, req),
                        10
                    )
                except asyncio.TimeoutError:
                    raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, "Error: timeout executing STAC API search.")

                if not features:
                    raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, "Error: STAC API Search returned no results.")

                try:
                    # 20 seconds should be enough to read the info from a COG, but may take longer on a non-COG
                    mosaicjson = await wait_for(
                        loop.run_in_executor(
                            None,
                            extract_mosaicjson_from_features,
                            features,
                            req.asset_name if req.asset_name else "visual"),
                        20
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
                
                return mosaicjson
                
            except HTTPException as e:
                raise e
            except Exception as e:
                raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, f"Error: {e}")

        def execute_stac_search(mosaic_request: StacApiQueryRequestBody) -> List[dict]:
            try:
                return Client.open(mosaic_request.stac_api_root).search(
                    ## **mosaic_request.dict(), ?? this feel a little unsafe
                    ids=mosaic_request.ids,
                    collections=mosaic_request.collections,
                    datetime=mosaic_request.datetime,
                    bbox=mosaic_request.bbox,
                    intersects=mosaic_request.intersects,
                    query=mosaic_request.query,
                    max_items=1000,  # todo: should this be a parameter? should an error be returned if more than 1000 in query?
                    limit=500
                    # setting limit to a higher value causes an error https://github.com/stac-utils/pystac-client/issues/56
                ).items_as_collection().to_dict()['features']
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
                except Exception as e:
                    raise Exception(f"Error extracting mosaic data from results: {e}")
            else:
                return None

        # todo: make this safer in case visual doesn't exist
        # how to handle others?
        # support for selection by role?
        def asset_href(feature: dict, asset_name: str) -> str:
            return feature["assets"][asset_name]["href"]

        # def mk_src_path(mosaic_id: str) -> str:
        #     return f"s3://the-bucket/{mosaic_id}.json.gz"
        #
        # def store(mj_id: str, mosaicjson: MosaicJSON, overwrite: bool = False) -> None:
        #     src_path = mk_src_path(mj_id)
        #     with rasterio.Env(**self.gdal_config):
        #         with self.reader(src_path, mosaic_def=mosaicjson) as mosaic:
        #             mosaic.write(overwrite=overwrite)
        #
        # def retrieve(mj_id: str) -> MosaicJSON:
        #     src_path = mk_src_path(mj_id)
        #     with rasterio.Env(**self.gdal_config):
        #         with self.reader(src_path,
        #                          reader=self.dataset_reader,
        #                          reader_options=self.reader_options,
        #                          **self.backend_options) as mosaic:
        #             return mosaic.mosaic_def

        def store(mj_id: str, mosaicjson: MosaicJSON, overwrite: bool = False) -> None:
            mj_store[mj_id] = mosaicjson

        def retrieve(mj_id: str) -> MosaicJSON:
            return mj_store[mj_id]


        def mk_mosaic_entity(mosaic_id, self_uri, base_uri, mosaicjson: Optional[MosaicJSON] = None):
            return MosaicEntity(
                id=mosaic_id,
                mosaicjson=mosaicjson, # todo: remove this, maybe?
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
                        href=f"{base_uri}/mosaicjson/tiles/{{z}}/{{x}}/{{y}}@1x?url={self_uri}/mosaicjson",
                        type="application/json",
                        title="Tiles Endpoint"
                    ),
                    Link(
                        rel="tiles-zxy",
                        href=f"{base_uri}/mosaicjson/tiles/{{z}}/{{x}}/{{y}}?url={self_uri}/mosaicjson",
                        type="application/json",
                        title="Tiles Endpoint /{z}/{x}/{y}"
                    ),
                    Link(
                        rel="tiles-zxy-format",
                        href=f"{base_uri}/mosaicjson/tiles/{{z}}/{{x}}/{{y}}.{{format}}?url={self_uri}/mosaicjson",
                        type="application/json",
                        title="Tiles Endpoint /{z}/{x}/{y}.{format}"
                    ),
                    Link(
                        rel="tiles-zxy-scale",
                        href=f"{base_uri}/mosaicjson/tiles/{{z}}/{{x}}/{{y}}@{{scale}}x?url={self_uri}/mosaicjson",
                        type="application/json",
                        title="Tiles Endpoint /{z}/{x}/{y}@{scale}x"
                    ),
                    Link(
                        rel="tiles-zxy-scale-format",
                        href=f"{base_uri}/mosaicjson/tiles/{{z}}/{{x}}/{{y}}@{{scale}}x.{{format}}?url={self_uri}/mosaicjson",
                        type="application/json",
                        title="Tiles Endpoint /{z}/{x}/{y}@{scale}x.{format}"
                    ),
                ])
