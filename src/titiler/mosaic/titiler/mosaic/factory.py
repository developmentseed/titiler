"""TiTiler.mosaic Router factories."""

import os
from typing import Any, Callable, Dict, List, Literal, Optional, Set, Tuple, Type, Union
from urllib.parse import urlencode

import rasterio
from attrs import define, field
from cogeo_mosaic.backends import BaseBackend, MosaicBackend
from cogeo_mosaic.models import Info as mosaicInfo
from cogeo_mosaic.mosaic import MosaicJSON
from fastapi import Depends, HTTPException, Path, Query
from geojson_pydantic.features import Feature
from geojson_pydantic.geometries import Polygon
from morecantile import tms as morecantile_tms
from morecantile.defaults import TileMatrixSets
from morecantile.models import crs_axis_inverted
from pydantic import Field
from rio_tiler.constants import MAX_THREADS, WGS84_CRS
from rio_tiler.io import BaseReader, MultiBandReader, MultiBaseReader, Reader
from rio_tiler.models import Bounds
from rio_tiler.mosaic.methods import PixelSelectionMethod
from rio_tiler.mosaic.methods.base import MosaicMethodBase
from rio_tiler.types import ColorMapType
from rio_tiler.utils import CRS_to_uri, CRS_to_urn
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from starlette.routing import NoMatchFound
from starlette.templating import Jinja2Templates
from typing_extensions import Annotated

from titiler.core.algorithm import BaseAlgorithm
from titiler.core.algorithm import algorithms as available_algorithms
from titiler.core.dependencies import (
    BidxExprParams,
    ColorMapParams,
    CoordCRSParams,
    CRSParams,
    DatasetParams,
    DefaultDependency,
    ImageRenderingParams,
    TileParams,
)
from titiler.core.factory import DEFAULT_TEMPLATES, BaseFactory, img_endpoint_params
from titiler.core.models.mapbox import TileJSON
from titiler.core.models.OGC import TileSet, TileSetList
from titiler.core.resources.enums import ImageType, OptionalHeader
from titiler.core.resources.responses import GeoJSONResponse, JSONResponse, XMLResponse
from titiler.core.utils import bounds_to_geometry, render_image
from titiler.mosaic.models.responses import Point

MOSAIC_THREADS = int(os.getenv("MOSAIC_CONCURRENCY", MAX_THREADS))
MOSAIC_STRICT_ZOOM = str(os.getenv("MOSAIC_STRICT_ZOOM", False)).lower() in [
    "true",
    "yes",
]


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

    backend: Type[BaseBackend] = MosaicBackend
    backend_dependency: Type[DefaultDependency] = DefaultDependency

    dataset_reader: Union[
        Type[BaseReader],
        Type[MultiBaseReader],
        Type[MultiBandReader],
    ] = Reader
    reader_dependency: Type[DefaultDependency] = DefaultDependency

    # Path Dependency
    path_dependency: Callable[..., Any] = DatasetPathParams

    # Backend.get_assets() Options
    assets_accessor_dependency: Type[DefaultDependency] = DefaultDependency

    # Indexes/Expression Dependencies
    layer_dependency: Type[DefaultDependency] = BidxExprParams

    # Rasterio Dataset Options (nodata, unscale, resampling, reproject)
    dataset_dependency: Type[DefaultDependency] = DatasetParams

    # Tile/Tilejson/WMTS Dependencies
    tile_dependency: Type[DefaultDependency] = TileParams

    # Post Processing Dependencies (algorithm)
    process_dependency: Callable[..., Optional[BaseAlgorithm]] = (
        available_algorithms.dependency
    )

    # Image rendering Dependencies
    colormap_dependency: Callable[..., Optional[ColorMapType]] = ColorMapParams
    render_dependency: Type[DefaultDependency] = ImageRenderingParams

    pixel_selection_dependency: Callable[..., MosaicMethodBase] = PixelSelectionParams

    # GDAL ENV dependency
    environment_dependency: Callable[..., Dict] = field(default=lambda: {})

    supported_tms: TileMatrixSets = morecantile_tms

    templates: Jinja2Templates = DEFAULT_TEMPLATES

    render_func: Callable[..., Tuple[bytes, str]] = render_image

    optional_headers: List[OptionalHeader] = field(factory=list)

    # Add/Remove some endpoints
    add_viewer: bool = True

    conforms_to: Set[str] = field(
        factory=lambda: {
            # https://docs.ogc.org/is/20-057/20-057.html#toc30
            "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/req/tileset",
            # https://docs.ogc.org/is/20-057/20-057.html#toc34
            "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/req/tilesets-list",
            # https://docs.ogc.org/is/20-057/20-057.html#toc65
            "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/req/core",
            "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/req/png",
            "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/req/jpeg",
            "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/req/tiff",
        }
    )

    def register_routes(self):
        """This Method register routes to the router."""

        self.read()
        self.bounds()
        self.info()
        self.tilesets()
        self.tile()
        if self.add_viewer:
            self.map_viewer()
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
            "/",
            response_model=MosaicJSON,
            response_model_exclude_none=True,
            responses={200: {"description": "Return MosaicJSON definition"}},
            operation_id=f"{self.operation_prefix}getMosaicJSON",
        )
        def read(
            src_path=Depends(self.path_dependency),
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Read a MosaicJSON"""
            with rasterio.Env(**env):
                with self.backend(
                    src_path,
                    reader=self.dataset_reader,
                    reader_options=reader_params.as_dict(),
                    **backend_params.as_dict(),
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
            operation_id=f"{self.operation_prefix}getBounds",
        )
        def bounds(
            src_path=Depends(self.path_dependency),
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            crs=Depends(CRSParams),
            env=Depends(self.environment_dependency),
        ):
            """Return the bounds of the MosaicJSON."""
            with rasterio.Env(**env):
                with self.backend(
                    src_path,
                    reader=self.dataset_reader,
                    reader_options=reader_params.as_dict(),
                    **backend_params.as_dict(),
                ) as src_dst:
                    crs = crs or WGS84_CRS
                    return {
                        "bounds": src_dst.get_geographic_bounds(crs or WGS84_CRS),
                        "crs": CRS_to_uri(crs) or crs.to_wkt(),
                    }

    ############################################################################
    # /info
    ############################################################################
    def info(self):
        """Register /info endpoint"""

        @self.router.get(
            "/info",
            response_model=mosaicInfo,
            responses={200: {"description": "Return info about the MosaicJSON"}},
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
                with self.backend(
                    src_path,
                    reader=self.dataset_reader,
                    reader_options=reader_params.as_dict(),
                    **backend_params.as_dict(),
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
    def tilesets(self):
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
        ):
            """Retrieve a list of available raster tilesets for the specified dataset."""
            with rasterio.Env(**env):
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

            tilesets = []
            for tms in self.supported_tms.list():
                tileset = {
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
                            "rel": "http://www.opengis.net/def/rel/ogc/1.0/tiling-schemes",
                            "type": "application/json",
                            "title": f"Definition of '{tms}' tileMatrixSet",
                        }
                    )
                except NoMatchFound:
                    pass

                tilesets.append(tileset)

            data = TileSetList.model_validate({"tilesets": tilesets})
            return data

        @self.router.get(
            "/tiles/{tileMatrixSetId}",
            response_model=TileSet,
            response_class=JSONResponse,
            response_model_exclude_none=True,
            responses={200: {"content": {"application/json": {}}}},
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
        ):
            """Retrieve the raster tileset metadata for the specified dataset and tiling scheme (tile matrix set)."""
            tms = self.supported_tms.get(tileMatrixSetId)
            with rasterio.Env(**env):
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

                    tilematrix_limit = []
                    for zoom in range(minzoom, maxzoom + 1, 1):
                        matrix = tms.matrix(zoom)
                        ulTile = tms.tile(bounds[0], bounds[3], int(matrix.id))
                        lrTile = tms.tile(bounds[2], bounds[1], int(matrix.id))
                        minx, maxx = (min(ulTile.x, lrTile.x), max(ulTile.x, lrTile.x))
                        miny, maxy = (min(ulTile.y, lrTile.y), max(ulTile.y, lrTile.y))
                        tilematrix_limit.append(
                            {
                                "tileMatrix": matrix.id,
                                "minTileRow": max(miny, 0),
                                "maxTileRow": min(maxy, matrix.matrixHeight),
                                "minTileCol": max(minx, 0),
                                "maxTileCol": min(maxx, matrix.matrixWidth),
                            }
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
                        "rel": "http://www.opengis.net/def/rel/ogc/1.0/tiling-schemes",
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
                    "tileMatrixSetLimits": tilematrix_limit,
                }
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
                ImageType,
                "Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
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
                        pixel_selection=pixel_selection,
                        tilesize=scale * 256,
                        threads=MOSAIC_THREADS,
                        **tile_params.as_dict(),
                        **layer_params.as_dict(),
                        **dataset_params.as_dict(),
                        **assets_accessor_params.as_dict(),
                    )

            if post_process:
                image = post_process(image)

            content, media_type = self.render_func(
                image,
                output_format=format,
                colormap=colormap,
                **render_params.as_dict(),
            )

            headers: Dict[str, str] = {}
            if OptionalHeader.x_assets in self.optional_headers:
                headers["X-Assets"] = ",".join(assets)

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
                Optional[ImageType],
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
                Optional[int],
                Query(description="Overwrite default minzoom."),
            ] = None,
            maxzoom: Annotated[
                Optional[int],
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
                with self.backend(
                    src_path,
                    tms=tms,
                    reader=self.dataset_reader,
                    reader_options=reader_params.as_dict(),
                    **backend_params.as_dict(),
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
                Optional[ImageType],
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
                Optional[int],
                Query(description="Overwrite default minzoom."),
            ] = None,
            maxzoom: Annotated[
                Optional[int],
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

    def wmts(self):  # noqa: C901
        """Add wmts endpoint."""

        @self.router.get(
            "/{tileMatrixSetId}/WMTSCapabilities.xml",
            response_class=XMLResponse,
            operation_id=f"{self.operation_prefix}getWMTS",
        )
        def wmts(
            request: Request,
            tileMatrixSetId: Annotated[
                Literal[tuple(self.supported_tms.list())],
                Path(
                    description="Identifier selecting one of the TileMatrixSetId supported."
                ),
            ],
            tile_format: Annotated[
                ImageType,
                Query(description="Output image type. Default is png."),
            ] = ImageType.png,
            tile_scale: Annotated[
                int,
                Query(
                    gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
                ),
            ] = 1,
            minzoom: Annotated[
                Optional[int],
                Query(description="Overwrite default minzoom."),
            ] = None,
            maxzoom: Annotated[
                Optional[int],
                Query(description="Overwrite default maxzoom."),
            ] = None,
            use_epsg: Annotated[
                bool,
                Query(
                    description="Use EPSG code, not opengis.net, for the ows:SupportedCRS in the TileMatrixSet (set to True to enable ArcMap compatability)"
                ),
            ] = False,
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
            """OGC WMTS endpoint."""
            route_params = {
                "z": "{TileMatrix}",
                "x": "{TileCol}",
                "y": "{TileRow}",
                "scale": tile_scale,
                "format": tile_format.value,
                "tileMatrixSetId": tileMatrixSetId,
            }
            tiles_url = self.url_for(request, "tile", **route_params)

            qs_key_to_remove = [
                "tilematrixsetid",
                "tile_format",
                "tile_scale",
                "minzoom",
                "maxzoom",
                "service",
                "use_epsg",
                "request",
            ]
            qs = [
                (key, value)
                for (key, value) in request.query_params._list
                if key.lower() not in qs_key_to_remove
            ]

            tms = self.supported_tms.get(tileMatrixSetId)
            with rasterio.Env(**env):
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

            tileMatrix = []
            for zoom in range(minzoom, maxzoom + 1):  # type: ignore
                matrix = tms.matrix(zoom)
                tm = f"""
                        <TileMatrix>
                            <ows:Identifier>{matrix.id}</ows:Identifier>
                            <ScaleDenominator>{matrix.scaleDenominator}</ScaleDenominator>
                            <TopLeftCorner>{matrix.pointOfOrigin[0]} {matrix.pointOfOrigin[1]}</TopLeftCorner>
                            <TileWidth>{matrix.tileWidth}</TileWidth>
                            <TileHeight>{matrix.tileHeight}</TileHeight>
                            <MatrixWidth>{matrix.matrixWidth}</MatrixWidth>
                            <MatrixHeight>{matrix.matrixHeight}</MatrixHeight>
                        </TileMatrix>"""
                tileMatrix.append(tm)

            if use_epsg:
                supported_crs = f"EPSG:{tms.crs.to_epsg()}"
            else:
                supported_crs = tms.crs.srs

            layers = [
                {
                    "title": (
                        src_path if isinstance(src_path, str) else "TiTiler Mosaic"
                    ),
                    "name": "default",
                    "tiles_url": tiles_url,
                    "query_string": urlencode(qs, doseq=True) if qs else None,
                    "bounds": bounds,
                },
            ]

            bbox_crs_type = "WGS84BoundingBox"
            bbox_crs_uri = "urn:ogc:def:crs:OGC:2:84"
            if tms.rasterio_geographic_crs != WGS84_CRS:
                bbox_crs_type = "BoundingBox"
                bbox_crs_uri = CRS_to_urn(tms.rasterio_geographic_crs)
                # WGS88BoundingBox is always xy ordered, but BoundingBox must match the CRS order
                if crs_axis_inverted(tms.geographic_crs):
                    # match the bounding box coordinate order to the CRS
                    bounds = [bounds[1], bounds[0], bounds[3], bounds[2]]

            return self.templates.TemplateResponse(
                request,
                name="wmts.xml",
                context={
                    "tileMatrixSetId": tms.id,
                    "tileMatrix": tileMatrix,
                    "supported_crs": supported_crs,
                    "bbox_crs_type": bbox_crs_type,
                    "bbox_crs_uri": bbox_crs_uri,
                    "layers": layers,
                    "media_type": tile_format.mediatype,
                },
                media_type="application/xml",
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
            response: Response,
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
                        threads=MOSAIC_THREADS,
                        **layer_params.as_dict(),
                        **dataset_params.as_dict(),
                        **assets_accessor_params.as_dict(),
                    )

            return {
                "coordinates": [lon, lat],
                "values": [
                    (src, pts.array.tolist(), pts.band_names) for src, pts in values
                ],
            }

    def validate(self):
        """Register /validate endpoint."""

        @self.router.post(
            "/validate",
            operation_id=f"{self.operation_prefix}validate",
        )
        def validate(body: MosaicJSON):
            """Validate a MosaicJSON"""
            return True

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
