"""TiTiler.mosaic Router factories."""

import logging
import os
from collections.abc import Callable
from typing import Annotated, Any, Literal
from urllib.parse import urlencode

import rasterio
from attrs import define, field
from fastapi import Body, Depends, HTTPException, Path, Query
from geojson_pydantic.features import Feature, FeatureCollection
from geojson_pydantic.geometries import Polygon
from morecantile import tms as morecantile_tms
from morecantile.defaults import TileMatrixSets
from pydantic import Field
from rio_tiler.constants import MAX_THREADS, WGS84_CRS
from rio_tiler.io import BaseReader, MultiBandReader, MultiBaseReader, Reader
from rio_tiler.mosaic.backend import BaseBackend, MosaicInfo
from rio_tiler.mosaic.methods import PixelSelectionMethod
from rio_tiler.mosaic.methods.base import MosaicMethodBase
from rio_tiler.types import ColorMapType
from rio_tiler.utils import CRS_to_uri
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from starlette.routing import NoMatchFound

from titiler.core.algorithm import BaseAlgorithm
from titiler.core.algorithm import algorithms as available_algorithms
from titiler.core.dependencies import (
    BidxExprParams,
    ColorMapParams,
    CoordCRSParams,
    CRSParams,
    DatasetParams,
    DefaultDependency,
    DstCRSParams,
    HistogramParams,
    ImageRenderingParams,
    OGCMapsParams,
    PartFeatureParams,
    StatisticsParams,
    TileParams,
)
from titiler.core.factory import BaseFactory, img_endpoint_params
from titiler.core.models.mapbox import TileJSON
from titiler.core.models.OGC import TileSet, TileSetList
from titiler.core.models.responses import StatisticsGeoJSON
from titiler.core.resources.enums import ImageType, MediaType, OptionalHeader
from titiler.core.resources.responses import GeoJSONResponse, JSONResponse
from titiler.core.utils import (
    accept_media_type,
    bounds_to_geometry,
    create_html_response,
    render_image,
    tms_limits,
)
from titiler.mosaic.models.responses import Point

MOSAIC_THREADS = int(os.getenv("MOSAIC_CONCURRENCY", MAX_THREADS))
MOSAIC_STRICT_ZOOM = str(os.getenv("MOSAIC_STRICT_ZOOM", False)).lower() in [
    "true",
    "yes",
]

logger = logging.getLogger(__name__)


def PixelSelectionParams(
    pixel_selection: Annotated[  # type: ignore
        Literal[tuple([e.name for e in PixelSelectionMethod])],
        Query(description="Pixel selection method."),
    ] = "first",
) -> MosaicMethodBase:
    """
    Returns the mosaic method used to combine datasets together.
    """
    return PixelSelectionMethod[pixel_selection].value()


def DatasetPathParams(url: Annotated[str, Query(description="Mosaic URL")]) -> str:
    """Create dataset path from args"""
    return url


@define(kw_only=True)
class MosaicTilerFactory(BaseFactory):
    """MosaicTiler Factory."""

    backend: type[BaseBackend]
    backend_dependency: type[DefaultDependency] = DefaultDependency

    dataset_reader: type[BaseReader] | type[MultiBaseReader] | type[MultiBandReader] = (
        Reader
    )
    reader_dependency: type[DefaultDependency] = DefaultDependency

    # Path Dependency
    path_dependency: Callable[..., Any] = DatasetPathParams

    # Backend.get_assets() Options
    assets_accessor_dependency: type[DefaultDependency] = DefaultDependency

    # Indexes/Expression Dependencies
    layer_dependency: type[DefaultDependency] = BidxExprParams

    # Rasterio Dataset Options (nodata, unscale, resampling, reproject)
    dataset_dependency: type[DefaultDependency] = DatasetParams

    # Tile/Tilejson Dependencies
    tile_dependency: type[DefaultDependency] = TileParams

    # Post Processing Dependencies (algorithm)
    process_dependency: Callable[..., BaseAlgorithm | None] = (
        available_algorithms.dependency
    )

    # Statistics/Histogram Dependencies
    stats_dependency: type[DefaultDependency] = StatisticsParams
    histogram_dependency: type[DefaultDependency] = HistogramParams

    # Crop endpoints Dependencies
    img_part_dependency: type[DefaultDependency] = PartFeatureParams

    # Image rendering Dependencies
    colormap_dependency: Callable[..., ColorMapType | None] = ColorMapParams
    render_dependency: type[DefaultDependency] = ImageRenderingParams

    pixel_selection_dependency: Callable[..., MosaicMethodBase] = PixelSelectionParams

    # GDAL ENV dependency
    environment_dependency: Callable[..., dict] = field(default=lambda: {})

    supported_tms: TileMatrixSets = morecantile_tms

    render_func: Callable[..., tuple[bytes, str]] = render_image

    optional_headers: list[OptionalHeader] = field(factory=list)

    # Add/Remove some endpoints
    add_viewer: bool = True
    add_statistics: bool = False
    add_part: bool = False
    add_ogc_maps: bool = False

    conforms_to: set[str] = field(
        factory=lambda: {
            # https://docs.ogc.org/is/20-057/20-057.html#toc30
            "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/tileset",
            # https://docs.ogc.org/is/20-057/20-057.html#toc34
            "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/tilesets-list",
            # https://docs.ogc.org/is/20-057/20-057.html#toc65
            "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/core",
            "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/png",
            "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/jpeg",
            "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/tiff",
        }
    )

    def register_routes(self):
        """This Method register routes to the router."""

        self.info()
        self.tilesets()
        self.tile()
        if self.add_viewer:
            self.map_viewer()
        self.tilejson()
        self.point()
        self.assets()

        if self.add_part:
            self.part()

        if self.add_statistics:
            self.statistics()

        if self.add_ogc_maps:
            self.ogc_maps()

    ############################################################################
    # /info
    ############################################################################
    def info(self):
        """Register /info endpoint"""

        @self.router.get(
            "/info",
            responses={
                200: {
                    "description": "Return info about the MosaicJSON",
                    "model": MosaicInfo,
                }
            },
            operation_id=f"{self.operation_prefix}getInfo",
        )
        def info(
            src_path=Depends(self.path_dependency),
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return basic info."""
            with rasterio.Env(**env):
                logger.info(
                    f"opening data with backend: {self.backend} and reader {self.dataset_reader}"
                )
                with self.backend(
                    src_path,
                    reader=self.dataset_reader,
                    reader_options=reader_params.as_dict(),
                    **backend_params.as_dict(),
                ) as src_dst:
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
                    "model": Feature[Polygon, MosaicInfo],
                }
            },
            operation_id=f"{self.operation_prefix}getInfoGeoJSON",
        )
        def info_geojson(
            src_path=Depends(self.path_dependency),
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            crs=Depends(CRSParams),
            env=Depends(self.environment_dependency),
        ):
            """Return mosaic's basic info as a GeoJSON feature."""
            with rasterio.Env(**env):
                logger.info(
                    f"opening data with backend: {self.backend} and reader {self.dataset_reader}"
                )
                with self.backend(
                    src_path,
                    reader=self.dataset_reader,
                    reader_options=reader_params.as_dict(),
                    **backend_params.as_dict(),
                ) as src_dst:
                    bounds = src_dst.get_geographic_bounds(crs or WGS84_CRS)
                    geometry = bounds_to_geometry(bounds)

                    return Feature(
                        type="Feature",
                        bbox=bounds,
                        geometry=geometry,
                        properties=src_dst.info(),
                    )

    ############################################################################
    # /tileset
    ############################################################################
    def tilesets(self):  # noqa: C901
        """Register OGC tilesets endpoints."""

        @self.router.get(
            "/tiles",
            response_model=TileSetList,
            response_class=JSONResponse,
            response_model_exclude_none=True,
            responses={
                200: {
                    "content": {
                        "application/json": {},
                        "text/html": {},
                    }
                }
            },
            summary="Retrieve a list of available raster tilesets for the specified dataset.",
            operation_id=f"{self.operation_prefix}getTileSetList",
        )
        async def tileset_list(
            request: Request,
            src_path=Depends(self.path_dependency),
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            crs=Depends(CRSParams),
            env=Depends(self.environment_dependency),
            f: Annotated[
                Literal["html", "json"] | None,
                Query(
                    description="Response MediaType. Defaults to endpoint's default or value defined in `accept` header."
                ),
            ] = None,
        ):
            """Retrieve a list of available raster tilesets for the specified dataset."""
            with rasterio.Env(**env):
                logger.info(
                    f"opening data with backend: {self.backend} and reader {self.dataset_reader}"
                )
                with self.backend(
                    src_path,
                    reader=self.dataset_reader,
                    reader_options=reader_params.as_dict(),
                    **backend_params.as_dict(),
                ) as src_dst:
                    bounds = src_dst.get_geographic_bounds(crs or WGS84_CRS)

            collection_bbox = {
                "lowerLeft": [bounds[0], bounds[1]],
                "upperRight": [bounds[2], bounds[3]],
                "crs": CRS_to_uri(crs or WGS84_CRS),
            }

            qs = [
                (key, value)
                for (key, value) in request.query_params._list
                if key.lower() not in ["crs"]
            ]
            query_string = f"?{urlencode(qs)}" if qs else ""

            tilesets: list[dict[str, Any]] = []
            for tms in self.supported_tms.list():
                tileset: dict[str, Any] = {
                    "title": f"tileset tiled using {tms} TileMatrixSet",
                    "dataType": "map",
                    "crs": self.supported_tms.get(tms).crs,
                    "boundingBox": collection_bbox,
                    "links": [
                        {
                            "href": self.url_for(
                                request, "tileset", tileMatrixSetId=tms
                            )
                            + query_string,
                            "rel": "self",
                            "type": "application/json",
                            "title": f"Tileset tiled using {tms} TileMatrixSet",
                        },
                        {
                            "href": self.url_for(
                                request,
                                "tile",
                                tileMatrixSetId=tms,
                                z="{z}",
                                x="{x}",
                                y="{y}",
                            )
                            + query_string,
                            "rel": "tile",
                            "title": "Templated link for retrieving Raster tiles",
                        },
                    ],
                }

                try:
                    tileset["links"].append(
                        {
                            "href": str(
                                request.url_for("tilematrixset", tileMatrixSetId=tms)
                            ),
                            "rel": "http://www.opengis.net/def/rel/ogc/1.0/tiling-scheme",
                            "type": "application/json",
                            "title": f"Definition of '{tms}' tileMatrixSet",
                        }
                    )
                except NoMatchFound:
                    pass

                tilesets.append(tileset)

            data = TileSetList.model_validate({"tilesets": tilesets})

            if f:
                output_type = MediaType[f]
            else:
                accepted_media = [MediaType.html, MediaType.json]
                output_type = (
                    accept_media_type(request.headers.get("accept", ""), accepted_media)
                    or MediaType.json
                )

            if output_type == MediaType.html:
                return create_html_response(
                    request,
                    data.model_dump(exclude_none=True, mode="json"),
                    title="Tilesets",
                    template_name="tilesets",
                    templates=self.templates,
                )

            return data

        @self.router.get(
            "/tiles/{tileMatrixSetId}",
            response_model=TileSet,
            response_class=JSONResponse,
            response_model_exclude_none=True,
            responses={
                200: {
                    "content": {
                        "application/json": {},
                        "text/html": {},
                    }
                }
            },
            summary="Retrieve the raster tileset metadata for the specified dataset and tiling scheme (tile matrix set).",
            operation_id=f"{self.operation_prefix}getTileSet",
        )
        async def tileset(
            request: Request,
            tileMatrixSetId: Annotated[
                Literal[tuple(self.supported_tms.list())],
                Path(
                    description="Identifier selecting one of the TileMatrixSetId supported."
                ),
            ],
            src_path=Depends(self.path_dependency),
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
            f: Annotated[
                Literal["html", "json"] | None,
                Query(
                    description="Response MediaType. Defaults to endpoint's default or value defined in `accept` header."
                ),
            ] = None,
        ):
            """Retrieve the raster tileset metadata for the specified dataset and tiling scheme (tile matrix set)."""
            tms = self.supported_tms.get(tileMatrixSetId)
            with rasterio.Env(**env):
                logger.info(
                    f"opening data with backend: {self.backend} and reader {self.dataset_reader}"
                )
                with self.backend(
                    src_path,
                    tms=tms,
                    reader=self.dataset_reader,
                    reader_options=reader_params.as_dict(),
                    **backend_params.as_dict(),
                ) as src_dst:
                    bounds = src_dst.get_geographic_bounds(tms.rasterio_geographic_crs)
                    minzoom = src_dst.minzoom
                    maxzoom = src_dst.maxzoom

                    collection_bbox = {
                        "lowerLeft": [bounds[0], bounds[1]],
                        "upperRight": [bounds[2], bounds[3]],
                        "crs": CRS_to_uri(tms.rasterio_geographic_crs),
                    }

                    tilematrix_limits = tms_limits(
                        tms,
                        bounds,
                        zooms=(minzoom, maxzoom),
                    )

            query_string = (
                f"?{urlencode(request.query_params._list)}"
                if request.query_params._list
                else ""
            )

            links = [
                {
                    "href": self.url_for(
                        request,
                        "tileset",
                        tileMatrixSetId=tileMatrixSetId,
                    ),
                    "rel": "self",
                    "type": "application/json",
                    "title": f"Tileset tiled using {tileMatrixSetId} TileMatrixSet",
                },
                {
                    "href": self.url_for(
                        request,
                        "tile",
                        tileMatrixSetId=tileMatrixSetId,
                        z="{z}",
                        x="{x}",
                        y="{y}",
                    )
                    + query_string,
                    "rel": "tile",
                    "title": "Templated link for retrieving Raster tiles",
                    "templated": True,
                },
            ]
            try:
                links.append(
                    {
                        "href": str(
                            request.url_for(
                                "tilematrixset", tileMatrixSetId=tileMatrixSetId
                            )
                        ),
                        "rel": "http://www.opengis.net/def/rel/ogc/1.0/tiling-scheme",
                        "type": "application/json",
                        "title": f"Definition of '{tileMatrixSetId}' tileMatrixSet",
                    }
                )
            except NoMatchFound:
                pass

            if self.add_viewer:
                links.append(
                    {
                        "href": self.url_for(
                            request,
                            "map_viewer",
                            tileMatrixSetId=tileMatrixSetId,
                        )
                        + query_string,
                        "type": "text/html",
                        "rel": "data",
                        "title": f"Map viewer for '{tileMatrixSetId}' tileMatrixSet",
                    }
                )

            data = TileSet.model_validate(
                {
                    "title": f"tileset tiled using {tileMatrixSetId} TileMatrixSet",
                    "dataType": "map",
                    "crs": tms.crs,
                    "boundingBox": collection_bbox,
                    "links": links,
                    "tileMatrixSetLimits": tilematrix_limits,
                }
            )

            if f:
                output_type = MediaType[f]
            else:
                accepted_media = [MediaType.html, MediaType.json]
                output_type = (
                    accept_media_type(request.headers.get("accept", ""), accepted_media)
                    or MediaType.json
                )

            if output_type == MediaType.html:
                return create_html_response(
                    request,
                    data,
                    title=tileMatrixSetId,
                    template_name="tileset",
                    templates=self.templates,
                )

            return data

    ############################################################################
    # /tiles
    ############################################################################
    def tile(self):  # noqa: C901
        """Register /tiles endpoints."""

        @self.router.get(
            "/tiles/{tileMatrixSetId}/{z}/{x}/{y}",
            operation_id=f"{self.operation_prefix}getTile",
            **img_endpoint_params,
        )
        @self.router.get(
            "/tiles/{tileMatrixSetId}/{z}/{x}/{y}.{format}",
            operation_id=f"{self.operation_prefix}getTileWithFormat",
            **img_endpoint_params,
        )
        @self.router.get(
            "/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x",
            operation_id=f"{self.operation_prefix}getTileWithScale",
            **img_endpoint_params,
        )
        @self.router.get(
            "/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
            operation_id=f"{self.operation_prefix}getTileWithFormatAndScale",
            **img_endpoint_params,
        )
        def tile(
            z: Annotated[
                int,
                Path(
                    description="Identifier (Z) selecting one of the scales defined in the TileMatrixSet and representing the scaleDenominator the tile.",
                ),
            ],
            x: Annotated[
                int,
                Path(
                    description="Column (X) index of the tile on the selected TileMatrix. It cannot exceed the MatrixHeight-1 for the selected TileMatrix.",
                ),
            ],
            y: Annotated[
                int,
                Path(
                    description="Row (Y) index of the tile on the selected TileMatrix. It cannot exceed the MatrixWidth-1 for the selected TileMatrix.",
                ),
            ],
            tileMatrixSetId: Annotated[
                Literal[tuple(self.supported_tms.list())],
                Path(
                    description="Identifier selecting one of the TileMatrixSetId supported."
                ),
            ],
            scale: Annotated[
                int,
                Field(
                    gt=0, le=4, description="Tile size scale. 1=256x256, 2=512x512..."
                ),
            ] = 1,
            format: Annotated[
                ImageType | None,
                Field(
                    description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
                ),
            ] = None,
            src_path=Depends(self.path_dependency),
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            assets_accessor_params=Depends(self.assets_accessor_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            pixel_selection=Depends(self.pixel_selection_dependency),
            tile_params=Depends(self.tile_dependency),
            post_process=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create map tile from a COG."""
            if scale < 1 or scale > 4:
                raise HTTPException(
                    400,
                    f"Invalid 'scale' parameter: {scale}. Scale HAVE TO be between 1 and 4",
                )

            tms = self.supported_tms.get(tileMatrixSetId)
            with rasterio.Env(**env):
                logger.info(
                    f"opening data with backend: {self.backend} and reader {self.dataset_reader}"
                )
                with self.backend(
                    src_path,
                    tms=tms,
                    reader=self.dataset_reader,
                    reader_options=reader_params.as_dict(),
                    **backend_params.as_dict(),
                ) as src_dst:
                    if MOSAIC_STRICT_ZOOM and (
                        z < src_dst.minzoom or z > src_dst.maxzoom
                    ):
                        raise HTTPException(
                            400,
                            f"Invalid ZOOM level {z}. Should be between {src_dst.minzoom} and {src_dst.maxzoom}",
                        )

                    image, assets = src_dst.tile(
                        x,
                        y,
                        z,
                        tilesize=scale * 256,
                        search_options=assets_accessor_params.as_dict(),
                        pixel_selection=pixel_selection,
                        threads=MOSAIC_THREADS,
                        **tile_params.as_dict(),
                        **layer_params.as_dict(),
                        **dataset_params.as_dict(),
                    )

            if post_process:
                image = post_process(image)

            content, media_type = self.render_func(
                image,
                output_format=format,
                colormap=colormap,
                **render_params.as_dict(),
            )

            headers: dict[str, str] = {}
            if OptionalHeader.x_assets in self.optional_headers:
                headers["X-Assets"] = ",".join(assets)

            if image.bounds is not None:
                headers["Content-Bbox"] = ",".join(map(str, image.bounds))
            if uri := CRS_to_uri(image.crs):
                headers["Content-Crs"] = f"<{uri}>"

            if (
                OptionalHeader.server_timing in self.optional_headers
                and image.metadata.get("timings")
            ):
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in image.metadata["timings"]]
                )

            return Response(content, media_type=media_type, headers=headers)

    def tilejson(self):  # noqa: C901
        """Add tilejson endpoint."""

        @self.router.get(
            "/{tileMatrixSetId}/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
            operation_id=f"{self.operation_prefix}getTileJSON",
        )
        def tilejson(
            request: Request,
            tileMatrixSetId: Annotated[
                Literal[tuple(self.supported_tms.list())],
                Path(
                    description="Identifier selecting one of the TileMatrixSetId supported."
                ),
            ],
            tile_format: Annotated[
                ImageType | None,
                Query(
                    description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
                ),
            ] = None,
            tile_scale: Annotated[
                int,
                Query(
                    gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
                ),
            ] = 1,
            minzoom: Annotated[
                int | None,
                Query(description="Overwrite default minzoom."),
            ] = None,
            maxzoom: Annotated[
                int | None,
                Query(description="Overwrite default maxzoom."),
            ] = None,
            src_path=Depends(self.path_dependency),
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            assets_accessor_params=Depends(self.assets_accessor_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            pixel_selection=Depends(self.pixel_selection_dependency),
            tile_params=Depends(self.tile_dependency),
            post_process=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return TileJSON document for a COG."""
            route_params = {
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
                "scale": tile_scale,
                "tileMatrixSetId": tileMatrixSetId,
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

            tms = self.supported_tms.get(tileMatrixSetId)
            with rasterio.Env(**env):
                logger.info(
                    f"opening data with backend: {self.backend} and reader {self.dataset_reader}"
                )
                with self.backend(
                    src_path,
                    tms=tms,
                    reader=self.dataset_reader,
                    reader_options=reader_params.as_dict(),
                    **backend_params.as_dict(),
                ) as src_dst:
                    bounds = src_dst.get_geographic_bounds(tms.rasterio_geographic_crs)
                    minzoom = minzoom if minzoom is not None else src_dst.minzoom
                    maxzoom = maxzoom if maxzoom is not None else src_dst.maxzoom
                    center = (
                        (bounds[0] + bounds[2]) / 2,
                        (bounds[1] + bounds[3]) / 2,
                        minzoom,
                    )
                    return {
                        "bounds": bounds,
                        "center": center,
                        "minzoom": minzoom,
                        "maxzoom": maxzoom,
                        "tiles": [tiles_url],
                        "attribution": os.environ.get("TITILER_DEFAULT_ATTRIBUTION"),
                    }

    def map_viewer(self):  # noqa: C901
        """Register /map.html endpoint."""

        @self.router.get(
            "/{tileMatrixSetId}/map.html",
            response_class=HTMLResponse,
            operation_id=f"{self.operation_prefix}getMapViewer",
        )
        def map_viewer(
            request: Request,
            tileMatrixSetId: Annotated[
                Literal[tuple(self.supported_tms.list())],
                Path(
                    description="Identifier selecting one of the TileMatrixSetId supported."
                ),
            ],
            tile_format: Annotated[
                ImageType | None,
                Query(
                    description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
                ),
            ] = None,
            tile_scale: Annotated[
                int,
                Query(
                    gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
                ),
            ] = 1,
            minzoom: Annotated[
                int | None,
                Query(description="Overwrite default minzoom."),
            ] = None,
            maxzoom: Annotated[
                int | None,
                Query(description="Overwrite default maxzoom."),
            ] = None,
            src_path=Depends(self.path_dependency),
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            assets_accessor_params=Depends(self.assets_accessor_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            pixel_selection=Depends(self.pixel_selection_dependency),
            tile_params=Depends(self.tile_dependency),
            post_process=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return TileJSON document for a dataset."""
            tilejson_url = self.url_for(
                request,
                "tilejson",
                tileMatrixSetId=tileMatrixSetId,
            )
            if request.query_params._list:
                tilejson_url += f"?{urlencode(request.query_params._list, doseq=True)}"

            tms = self.supported_tms.get(tileMatrixSetId)
            return self.templates.TemplateResponse(
                request,
                name="map.html",
                context={
                    "tilejson_endpoint": tilejson_url,
                    "tms": tms,
                    "resolutions": [matrix.cellSize for matrix in tms],
                },
                media_type="text/html",
            )

    ############################################################################
    # /point (Optional)
    ############################################################################
    def point(self):
        """Register /point endpoint."""

        @self.router.get(
            "/point/{lon},{lat}",
            response_model=Point,
            response_class=JSONResponse,
            responses={200: {"description": "Return a value for a point"}},
            operation_id=f"{self.operation_prefix}getDataForPoint",
        )
        def point(
            lon: Annotated[float, Path(description="Longitude")],
            lat: Annotated[float, Path(description="Latitude")],
            src_path=Depends(self.path_dependency),
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            assets_accessor_params=Depends(self.assets_accessor_dependency),
            coord_crs=Depends(CoordCRSParams),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Point value for a Mosaic."""
            with rasterio.Env(**env):
                logger.info(
                    f"opening data with backend: {self.backend} and reader {self.dataset_reader}"
                )
                with self.backend(
                    src_path,
                    reader=self.dataset_reader,
                    reader_options=reader_params.as_dict(),
                    **backend_params.as_dict(),
                ) as src_dst:
                    values = src_dst.point(
                        lon,
                        lat,
                        coord_crs=coord_crs or WGS84_CRS,
                        search_options=assets_accessor_params.as_dict(),
                        threads=MOSAIC_THREADS,
                        **layer_params.as_dict(),
                        **dataset_params.as_dict(),
                    )

            return {
                "coordinates": [lon, lat],
                "assets": [
                    {
                        "name": asset_name,
                        "values": pt.array.tolist(),
                        "band_names": pt.band_names,
                        "band_descriptions": pt.band_descriptions,
                    }
                    for asset_name, pt in values
                ],
            }

    def statistics(self):
        """Register /statistics endpoint."""

        @self.router.post(
            "/statistics",
            response_model=StatisticsGeoJSON,
            response_model_exclude_none=True,
            response_class=GeoJSONResponse,
            responses={
                200: {
                    "content": {"application/geo+json": {}},
                    "description": "Return statistics for geojson features.",
                }
            },
            operation_id=f"{self.operation_prefix}postStatisticsForGeoJSON",
        )
        def geojson_statistics(
            geojson: Annotated[
                FeatureCollection | Feature,
                Body(description="GeoJSON Feature or FeatureCollection."),
            ],
            src_path=Depends(self.path_dependency),
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            assets_accessor_params=Depends(self.assets_accessor_dependency),
            coord_crs=Depends(CoordCRSParams),
            dst_crs=Depends(DstCRSParams),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            pixel_selection=Depends(self.pixel_selection_dependency),
            image_params=Depends(self.img_part_dependency),
            post_process=Depends(self.process_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Statistics from a geojson feature or featureCollection."""
            fc = geojson
            if isinstance(fc, Feature):
                fc = FeatureCollection(type="FeatureCollection", features=[geojson])

            with rasterio.Env(**env):
                logger.info(
                    f"opening data with backend: {self.backend} and reader {self.dataset_reader}"
                )
                with self.backend(
                    src_path,
                    reader=self.dataset_reader,
                    reader_options=reader_params.as_dict(),
                    **backend_params.as_dict(),
                ) as src_dst:
                    for i, feature in enumerate(fc.features):
                        shape = feature.model_dump(exclude_none=True)

                        logger.info(f"feature {i}: reading data")
                        image, assets = src_dst.feature(
                            shape,
                            shape_crs=coord_crs or WGS84_CRS,
                            dst_crs=dst_crs,
                            align_bounds_with_dataset=True,
                            search_options=assets_accessor_params.as_dict(),
                            pixel_selection=pixel_selection,
                            threads=MOSAIC_THREADS,
                            **layer_params.as_dict(),
                            **dataset_params.as_dict(),
                            **image_params.as_dict(),
                        )

                        coverage_array = image.get_coverage_array(
                            shape,
                            shape_crs=coord_crs or WGS84_CRS,
                        )

                        if post_process:
                            logger.info(f"feature {i}: post processing image")
                            image = post_process(image)

                        logger.info(f"feature {i}: calculating statistics")
                        stats = image.statistics(
                            **stats_params.as_dict(),
                            hist_options=histogram_params.as_dict(),
                            coverage=coverage_array,
                        )

                        feature.properties = feature.properties or {}
                        feature.properties.update({"statistics": stats})
                        feature.properties.update({"used_assets": assets})

            return fc.features[0] if isinstance(geojson, Feature) else fc

    def part(self):  # noqa: C901
        """Register /bbox and /feature endpoint."""

        # GET endpoints
        @self.router.get(
            "/bbox/{minx},{miny},{maxx},{maxy}.{format}",
            operation_id=f"{self.operation_prefix}getDataForBoundingBoxWithFormat",
            **img_endpoint_params,
        )
        @self.router.get(
            "/bbox/{minx},{miny},{maxx},{maxy}/{width}x{height}.{format}",
            operation_id=f"{self.operation_prefix}getDataForBoundingBoxWithSizesAndFormat",
            **img_endpoint_params,
        )
        def bbox_image(
            minx: Annotated[float, Path(description="Bounding box min X")],
            miny: Annotated[float, Path(description="Bounding box min Y")],
            maxx: Annotated[float, Path(description="Bounding box max X")],
            maxy: Annotated[float, Path(description="Bounding box max Y")],
            format: Annotated[
                ImageType,
                Field(
                    description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg)."
                ),
            ],
            src_path=Depends(self.path_dependency),
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            assets_accessor_params=Depends(self.assets_accessor_dependency),
            coord_crs=Depends(CoordCRSParams),
            dst_crs=Depends(DstCRSParams),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            pixel_selection=Depends(self.pixel_selection_dependency),
            image_params=Depends(self.img_part_dependency),
            post_process=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create image from a bbox."""
            with rasterio.Env(**env):
                logger.info(
                    f"opening data with backend: {self.backend} and reader {self.dataset_reader}"
                )
                with self.backend(
                    src_path,
                    reader=self.dataset_reader,
                    reader_options=reader_params.as_dict(),
                    **backend_params.as_dict(),
                ) as src_dst:
                    image, assets = src_dst.part(
                        [minx, miny, maxx, maxy],
                        dst_crs=dst_crs,
                        bounds_crs=coord_crs or WGS84_CRS,
                        search_options=assets_accessor_params.as_dict(),
                        pixel_selection=pixel_selection,
                        threads=MOSAIC_THREADS,
                        **layer_params.as_dict(),
                        **dataset_params.as_dict(),
                        **image_params.as_dict(),
                    )
                    dst_colormap = getattr(src_dst, "colormap", None)

            if post_process:
                image = post_process(image)

            content, media_type = self.render_func(
                image,
                output_format=format,
                colormap=colormap or dst_colormap,
                **render_params.as_dict(),
            )

            headers: dict[str, str] = {}
            if OptionalHeader.x_assets in self.optional_headers:
                headers["X-Assets"] = ",".join(assets)

            if image.bounds is not None:
                headers["Content-Bbox"] = ",".join(map(str, image.bounds))
            if uri := CRS_to_uri(image.crs):
                headers["Content-Crs"] = f"<{uri}>"

            if (
                OptionalHeader.server_timing in self.optional_headers
                and image.metadata.get("timings")
            ):
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in image.metadata["timings"]]
                )

            return Response(content, media_type=media_type, headers=headers)

        @self.router.post(
            "/feature",
            operation_id=f"{self.operation_prefix}postDataForGeoJSON",
            **img_endpoint_params,
        )
        @self.router.post(
            "/feature.{format}",
            operation_id=f"{self.operation_prefix}postDataForGeoJSONWithFormat",
            **img_endpoint_params,
        )
        @self.router.post(
            "/feature/{width}x{height}.{format}",
            operation_id=f"{self.operation_prefix}postDataForGeoJSONWithSizesAndFormat",
            **img_endpoint_params,
        )
        def feature_image(
            geojson: Annotated[Feature, Body(description="GeoJSON Feature.")],
            src_path=Depends(self.path_dependency),
            format: Annotated[
                ImageType | None,
                Field(
                    description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg)."
                ),
            ] = None,
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            assets_accessor_params=Depends(self.assets_accessor_dependency),
            coord_crs=Depends(CoordCRSParams),
            dst_crs=Depends(DstCRSParams),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_part_dependency),
            pixel_selection=Depends(self.pixel_selection_dependency),
            post_process=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create image from a geojson feature."""
            with rasterio.Env(**env):
                logger.info(
                    f"opening data with backend: {self.backend} and reader {self.dataset_reader}"
                )
                with self.backend(
                    src_path,
                    reader=self.dataset_reader,
                    reader_options=reader_params.as_dict(),
                    **backend_params.as_dict(),
                ) as src_dst:
                    image, assets = src_dst.feature(
                        geojson.model_dump(exclude_none=True),
                        shape_crs=coord_crs or WGS84_CRS,
                        dst_crs=dst_crs,
                        search_options=assets_accessor_params.as_dict(),
                        pixel_selection=pixel_selection,
                        threads=MOSAIC_THREADS,
                        **layer_params.as_dict(),
                        **image_params.as_dict(),
                        **dataset_params.as_dict(),
                    )

            if post_process:
                image = post_process(image)

            content, media_type = self.render_func(
                image,
                output_format=format,
                colormap=colormap,
                **render_params.as_dict(),
            )

            headers: dict[str, str] = {}
            if OptionalHeader.x_assets in self.optional_headers:
                headers["X-Assets"] = ",".join(assets)

            if image.bounds is not None:
                headers["Content-Bbox"] = ",".join(map(str, image.bounds))
            if uri := CRS_to_uri(image.crs):
                headers["Content-Crs"] = f"<{uri}>"

            if (
                OptionalHeader.server_timing in self.optional_headers
                and image.metadata.get("timings")
            ):
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in image.metadata["timings"]]
                )

            return Response(content, media_type=media_type, headers=headers)

    def assets(self):
        """Register /assets endpoint."""

        @self.router.get(
            "/bbox/{minx},{miny},{maxx},{maxy}/assets",
            responses={200: {"description": "Return list of COGs in bounding box"}},
            operation_id=f"{self.operation_prefix}getAssetsForBoundingBox",
        )
        def assets_for_bbox(
            minx: Annotated[float, Path(description="Bounding box min X")],
            miny: Annotated[float, Path(description="Bounding box min Y")],
            maxx: Annotated[float, Path(description="Bounding box max X")],
            maxy: Annotated[float, Path(description="Bounding box max Y")],
            src_path=Depends(self.path_dependency),
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            assets_accessor_params=Depends(self.assets_accessor_dependency),
            coord_crs=Depends(CoordCRSParams),
            env=Depends(self.environment_dependency),
        ):
            """Return a list of assets which overlap a bounding box"""
            with rasterio.Env(**env):
                logger.info(
                    f"opening data with backend: {self.backend} and reader {self.dataset_reader}"
                )
                with self.backend(
                    src_path,
                    reader=self.dataset_reader,
                    reader_options=reader_params.as_dict(),
                    **backend_params.as_dict(),
                ) as src_dst:
                    return src_dst.assets_for_bbox(
                        minx,
                        miny,
                        maxx,
                        maxy,
                        coord_crs=coord_crs or WGS84_CRS,
                        **assets_accessor_params.as_dict(),
                    )

        @self.router.get(
            "/point/{lon},{lat}/assets",
            responses={200: {"description": "Return list of COGs"}},
            operation_id=f"{self.operation_prefix}getAssetsForPoint",
        )
        def assets_for_lon_lat(
            lon: Annotated[float, Path(description="Longitude")],
            lat: Annotated[float, Path(description="Latitude")],
            src_path=Depends(self.path_dependency),
            coord_crs=Depends(CoordCRSParams),
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            assets_accessor_params=Depends(self.assets_accessor_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return a list of assets which overlap a point"""
            with rasterio.Env(**env):
                logger.info(
                    f"opening data with backend: {self.backend} and reader {self.dataset_reader}"
                )
                with self.backend(
                    src_path,
                    reader=self.dataset_reader,
                    reader_options=reader_params.as_dict(),
                    **backend_params.as_dict(),
                ) as src_dst:
                    return src_dst.assets_for_point(
                        lon,
                        lat,
                        coord_crs=coord_crs or WGS84_CRS,
                        **assets_accessor_params.as_dict(),
                    )

        @self.router.get(
            "/tiles/{tileMatrixSetId}/{z}/{x}/{y}/assets",
            responses={200: {"description": "Return list of COGs"}},
            operation_id=f"{self.operation_prefix}getAssetsForTile",
        )
        def assets_for_tile(
            tileMatrixSetId: Annotated[
                Literal[tuple(self.supported_tms.list())],
                Path(
                    description="Identifier selecting one of the TileMatrixSetId supported."
                ),
            ],
            z: Annotated[
                int,
                Path(
                    description="Identifier (Z) selecting one of the scales defined in the TileMatrixSet and representing the scaleDenominator the tile.",
                ),
            ],
            x: Annotated[
                int,
                Path(
                    description="Column (X) index of the tile on the selected TileMatrix. It cannot exceed the MatrixHeight-1 for the selected TileMatrix.",
                ),
            ],
            y: Annotated[
                int,
                Path(
                    description="Row (Y) index of the tile on the selected TileMatrix. It cannot exceed the MatrixWidth-1 for the selected TileMatrix.",
                ),
            ],
            src_path=Depends(self.path_dependency),
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            assets_accessor_params=Depends(self.assets_accessor_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return a list of assets which overlap a given tile"""
            tms = self.supported_tms.get(tileMatrixSetId)
            with rasterio.Env(**env):
                logger.info(
                    f"opening data with backend: {self.backend} and reader {self.dataset_reader}"
                )
                with self.backend(
                    src_path,
                    tms=tms,
                    reader=self.dataset_reader,
                    reader_options=reader_params.as_dict(),
                    **backend_params.as_dict(),
                ) as src_dst:
                    return src_dst.assets_for_tile(
                        x,
                        y,
                        z,
                        **assets_accessor_params.as_dict(),
                    )

    ############################################################################
    # OGC Maps (Optional)
    ############################################################################
    def ogc_maps(self):  # noqa: C901
        """Register OGC Maps /map` endpoint."""

        self.conforms_to.update(
            {
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/core",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/crs",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/scaling",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/scaling/width-definition",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/scaling/height-definition",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/spatial-subsetting",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/spatial-subsetting/bbox-definition",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/spatial-subsetting/bbox-crs",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/spatial-subsetting/crs-curie",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/png",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/jpeg",
                "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/tiff",
            }
        )

        @self.router.get(
            "/map",
            operation_id=f"{self.operation_prefix}getMap",
            **img_endpoint_params,
        )
        def get_map(
            src_path=Depends(self.path_dependency),
            ogc_params=Depends(OGCMapsParams),
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            assets_accessor_params=Depends(self.assets_accessor_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            pixel_selection=Depends(self.pixel_selection_dependency),
            post_process=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            env=Depends(self.environment_dependency),
        ) -> Response:
            """OGC Maps API."""
            with rasterio.Env(**env):
                logger.info(
                    f"opening data with backend: {self.backend} and reader {self.dataset_reader}"
                )
                with self.backend(
                    src_path,
                    reader=self.dataset_reader,
                    reader_options=reader_params.as_dict(),
                    **backend_params.as_dict(),
                ) as src_dst:
                    if ogc_params.bbox is not None:
                        image, assets = src_dst.part(
                            ogc_params.bbox,
                            dst_crs=ogc_params.crs or src_dst.crs,
                            bounds_crs=ogc_params.bbox_crs or WGS84_CRS,
                            search_options=assets_accessor_params.as_dict(),
                            pixel_selection=pixel_selection,
                            threads=MOSAIC_THREADS,
                            width=ogc_params.width,
                            height=ogc_params.height,
                            max_size=ogc_params.max_size,
                            **layer_params.as_dict(),
                            **dataset_params.as_dict(),
                        )

                    else:
                        # NOTE: Defaults backends do not support preview
                        image, assets = src_dst.preview(
                            search_options=assets_accessor_params.as_dict(),
                            pixel_selection=pixel_selection,
                            threads=MOSAIC_THREADS,
                            width=ogc_params.width,
                            height=ogc_params.height,
                            max_size=ogc_params.max_size,
                            dst_crs=ogc_params.crs or src_dst.crs,
                            **layer_params.as_dict(),
                            **dataset_params.as_dict(),
                        )
                    dst_colormap = getattr(src_dst, "colormap", None)

            if post_process:
                image = post_process(image)

            content, media_type = self.render_func(
                image,
                output_format=ogc_params.format,
                colormap=colormap or dst_colormap,
                **render_params.as_dict(),
            )

            headers: dict[str, str] = {}
            if OptionalHeader.x_assets in self.optional_headers:
                headers["X-Assets"] = ",".join(assets)

            if image.bounds is not None:
                headers["Content-Bbox"] = ",".join(map(str, image.bounds))
            if uri := CRS_to_uri(image.crs):
                headers["Content-Crs"] = f"<{uri}>"

            if (
                OptionalHeader.server_timing in self.optional_headers
                and image.metadata.get("timings")
            ):
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in image.metadata["timings"]]
                )

            return Response(content, media_type=media_type, headers=headers)
