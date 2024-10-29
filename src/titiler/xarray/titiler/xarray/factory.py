"""TiTiler.xarray factory."""

from typing import Callable, List, Literal, Optional, Type, Union

import rasterio
from attrs import define, field
from fastapi import Body, Depends, Path, Query
from geojson_pydantic.features import Feature, FeatureCollection
from geojson_pydantic.geometries import MultiPolygon, Polygon
from pydantic import Field
from rio_tiler.constants import WGS84_CRS
from rio_tiler.models import Info
from starlette.responses import Response
from typing_extensions import Annotated

from titiler.core.dependencies import (
    CoordCRSParams,
    CRSParams,
    DatasetPathParams,
    DefaultDependency,
    DstCRSParams,
    HistogramParams,
    StatisticsParams,
)
from titiler.core.factory import TilerFactory as BaseTilerFactory
from titiler.core.factory import img_endpoint_params
from titiler.core.models.responses import InfoGeoJSON, StatisticsGeoJSON
from titiler.core.resources.enums import ImageType
from titiler.core.resources.responses import GeoJSONResponse, JSONResponse
from titiler.core.utils import render_image
from titiler.xarray.dependencies import (
    DatasetParams,
    PartFeatureParams,
    TileParams,
    XarrayIOParams,
    XarrayParams,
)
from titiler.xarray.io import Reader


@define(kw_only=True)
class TilerFactory(BaseTilerFactory):
    """Xarray Tiler Factory."""

    reader: Type[Reader] = Reader

    path_dependency: Callable[..., str] = DatasetPathParams

    reader_dependency: Type[DefaultDependency] = XarrayParams

    # Indexes/Expression Dependencies (Not layer dependencies for Xarray)
    layer_dependency: Type[DefaultDependency] = DefaultDependency

    # Dataset Options (nodata, reproject)
    dataset_dependency: Type[DefaultDependency] = DatasetParams

    # Tile/Tilejson/WMTS Dependencies (multiscale option)
    tile_dependency: Type[TileParams] = TileParams

    # Statistics/Histogram Dependencies
    stats_dependency: Type[DefaultDependency] = StatisticsParams
    histogram_dependency: Type[DefaultDependency] = HistogramParams

    img_part_dependency: Type[DefaultDependency] = PartFeatureParams

    # Custom dependency for /variable
    io_dependency: Type[DefaultDependency] = XarrayIOParams

    add_viewer: bool = True
    add_part: bool = True

    # remove some attribute from init
    img_preview_dependency: Type[DefaultDependency] = field(init=False)
    add_preview: bool = field(init=False)

    def register_routes(self):
        """Register routes to the router."""
        self.variables()
        self.bounds()
        self.info()
        self.tile()
        self.tilejson()
        self.wmts()
        self.point()
        self.statistics()

        if self.add_part:
            self.part()

        if self.add_viewer:
            self.map_viewer()

    def variables(self):
        """Register /variables endpoint."""

        @self.router.get(
            "/variables",
            response_model=List[str],
            responses={200: {"description": "Return Xarray Dataset variables."}},
        )
        def variables(
            src_path=Depends(self.path_dependency),
            io_params=Depends(self.io_dependency),
        ):
            """return available variables."""
            return self.reader.list_variables(src_path, **io_params.as_dict())

    # Custom /info endpoints (adds `show_times` options)
    def info(self):
        """Register /info endpoint."""

        @self.router.get(
            "/info",
            response_model=Info,
            response_model_exclude_none=True,
            response_class=JSONResponse,
            responses={200: {"description": "Return dataset's basic info."}},
        )
        def info_endpoint(
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            show_times: Annotated[
                Optional[bool],
                Query(description="Show info about the time dimension"),
            ] = None,
            env=Depends(self.environment_dependency),
        ) -> Info:
            """Return dataset's basic info."""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    info = src_dst.info().model_dump()
                    if show_times and "time" in src_dst.input.dims:
                        times = [str(x.data) for x in src_dst.input.time]
                        info["count"] = len(times)
                        info["times"] = times

            return Info(**info)

        @self.router.get(
            "/info.geojson",
            response_model=InfoGeoJSON,
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
            reader_params=Depends(self.reader_dependency),
            show_times: Annotated[
                Optional[bool],
                Query(description="Show info about the time dimension"),
            ] = None,
            crs=Depends(CRSParams),
            env=Depends(self.environment_dependency),
        ):
            """Return dataset's basic info as a GeoJSON feature."""
            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    bounds = src_dst.get_geographic_bounds(crs or WGS84_CRS)
                    if bounds[0] > bounds[2]:
                        pl = Polygon.from_bounds(-180, bounds[1], bounds[2], bounds[3])
                        pr = Polygon.from_bounds(bounds[0], bounds[1], 180, bounds[3])
                        geometry = MultiPolygon(
                            type="MultiPolygon",
                            coordinates=[pl.coordinates, pr.coordinates],
                        )
                    else:
                        geometry = Polygon.from_bounds(*bounds)

                    info = src_dst.info().model_dump()
                    if show_times and "time" in src_dst.input.dims:
                        times = [str(x.data) for x in src_dst.input.time]
                        info["count"] = len(times)
                        info["times"] = times

            return Feature(
                type="Feature",
                bbox=bounds,
                geometry=geometry,
                properties=info,
            )

    # custom /tiles endpoints (adds `multiscale` options)
    def tile(self):
        """Register /tiles endpoint."""

        @self.router.get(r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(
            r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}.{format}", **img_endpoint_params
        )
        @self.router.get(
            r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x", **img_endpoint_params
        )
        @self.router.get(
            r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
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
            multiscale: Annotated[
                Optional[bool],
                Query(
                    title="multiscale",
                    description="Whether the dataset has multiscale groups (Zoom levels)",
                ),
            ] = None,
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            tile_params=Depends(self.tile_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            post_process=Depends(self.process_dependency),
            rescale=Depends(self.rescale_dependency),
            color_formula=Depends(self.color_formula_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create map tile from a dataset."""
            tms = self.supported_tms.get(tileMatrixSetId)

            reader_options = reader_params.as_dict()
            if getattr(tile_params, "multiscale", False):
                reader_options["group"] = z

            with rasterio.Env(**env):
                with self.reader(src_path, tms=tms, **reader_options) as src_dst:
                    image = src_dst.tile(
                        x,
                        y,
                        z,
                        tilesize=scale * 256,
                        **layer_params.as_dict(),
                        **dataset_params.as_dict(),
                    )

            if post_process:
                image = post_process(image)

            if rescale:
                image.rescale(rescale)

            if color_formula:
                image.apply_color_formula(color_formula)

            content, media_type = render_image(
                image,
                output_format=format,
                colormap=colormap,
                **render_params.as_dict(),
            )

            return Response(content, media_type=media_type)

    # custom /statistics endpoints (remove /statistics - GET)
    def statistics(self):
        """add statistics endpoints."""

        # POST endpoint
        @self.router.post(
            "/statistics",
            response_model=StatisticsGeoJSON,
            response_model_exclude_none=True,
            response_class=GeoJSONResponse,
            responses={
                200: {
                    "content": {"application/geo+json": {}},
                    "description": "Return dataset's statistics from feature or featureCollection.",
                }
            },
        )
        def geojson_statistics(
            geojson: Annotated[
                Union[FeatureCollection, Feature],
                Body(description="GeoJSON Feature or FeatureCollection."),
            ],
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            coord_crs=Depends(CoordCRSParams),
            dst_crs=Depends(DstCRSParams),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
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
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    for feature in fc:
                        shape = feature.model_dump(exclude_none=True)
                        image = src_dst.feature(
                            shape,
                            shape_crs=coord_crs or WGS84_CRS,
                            dst_crs=dst_crs,
                            align_bounds_with_dataset=True,
                            **layer_params.as_dict(),
                            **image_params.as_dict(),
                            **dataset_params.as_dict(),
                        )

                        # Get the coverage % array
                        coverage_array = image.get_coverage_array(
                            shape,
                            shape_crs=coord_crs or WGS84_CRS,
                        )

                        if post_process:
                            image = post_process(image)

                        stats = image.statistics(
                            **stats_params.as_dict(),
                            hist_options=histogram_params.as_dict(),
                            coverage=coverage_array,
                        )

                        feature.properties = feature.properties or {}
                        feature.properties.update({"statistics": stats})

            return fc.features[0] if isinstance(geojson, Feature) else fc
