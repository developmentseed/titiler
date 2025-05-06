"""TiTiler.xarray factory."""

from typing import Callable, Optional, Type, Union

import rasterio
from attrs import define, field
from fastapi import Body, Depends, Query
from geojson_pydantic.features import Feature, FeatureCollection
from rio_tiler.constants import WGS84_CRS
from rio_tiler.models import Info
from typing_extensions import Annotated

from titiler.core.dependencies import (
    BidxParams,
    CoordCRSParams,
    CRSParams,
    DatasetPathParams,
    DefaultDependency,
    DstCRSParams,
    HistogramParams,
    StatisticsParams,
)
from titiler.core.factory import TilerFactory as BaseTilerFactory
from titiler.core.models.responses import InfoGeoJSON, StatisticsGeoJSON
from titiler.core.resources.responses import GeoJSONResponse, JSONResponse
from titiler.core.utils import bounds_to_geometry
from titiler.xarray.dependencies import DatasetParams, PartFeatureParams, XarrayParams
from titiler.xarray.io import Reader


@define(kw_only=True)
class TilerFactory(BaseTilerFactory):
    """Xarray Tiler Factory."""

    reader: Type[Reader] = Reader

    path_dependency: Callable[..., str] = DatasetPathParams

    reader_dependency: Type[DefaultDependency] = XarrayParams

    # Indexes Dependencies
    layer_dependency: Type[DefaultDependency] = BidxParams

    # Dataset Options (nodata, reproject)
    dataset_dependency: Type[DefaultDependency] = DatasetParams

    # Tile/Tilejson/WMTS Dependencies  (Not used in titiler.xarray)
    tile_dependency: Type[DefaultDependency] = DefaultDependency

    # Statistics/Histogram Dependencies
    stats_dependency: Type[DefaultDependency] = StatisticsParams
    histogram_dependency: Type[DefaultDependency] = HistogramParams

    img_part_dependency: Type[DefaultDependency] = PartFeatureParams

    add_viewer: bool = True
    add_part: bool = True

    # remove some attribute from init
    img_preview_dependency: Type[DefaultDependency] = field(init=False)
    add_preview: bool = field(init=False, default=False)

    # Custom /info endpoints (adds `show_times` options)
    def info(self):
        """Register /info endpoint."""

        @self.router.get(
            "/info",
            response_model=Info,
            response_model_exclude_none=True,
            response_class=JSONResponse,
            responses={200: {"description": "Return dataset's basic info."}},
            operation_id=f"{self.operation_prefix}getInfo",
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
            operation_id=f"{self.operation_prefix}getInfoGeoJSON",
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
                    geometry = bounds_to_geometry(bounds)
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
            operation_id=f"{self.operation_prefix}postStatisticsForGeoJSON",
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
                    for feature in fc.features:
                        shape = feature.model_dump(exclude_none=True)
                        image = src_dst.feature(
                            shape,
                            shape_crs=coord_crs or WGS84_CRS,
                            dst_crs=dst_crs,
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
