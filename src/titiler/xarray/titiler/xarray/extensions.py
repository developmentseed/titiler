"""titiler.xarray Extensions."""

import warnings
from typing import Callable, List, Optional, Type

import xarray
from attrs import define
from fastapi import Depends, Query
from rio_tiler.constants import WGS84_CRS
from starlette.responses import HTMLResponse
from typing_extensions import Annotated

from titiler.core.dependencies import DefaultDependency
from titiler.core.factory import FactoryExtension
from titiler.core.resources.enums import MediaType
from titiler.xarray.dependencies import XarrayIOParams
from titiler.xarray.factory import TilerFactory
from titiler.xarray.io import xarray_open_dataset


@define
class VariablesExtension(FactoryExtension):
    """Add /variables endpoint to a Xarray TilerFactory."""

    # Custom dependency for /variables
    io_dependency: Type[DefaultDependency] = XarrayIOParams
    dataset_opener: Callable[..., xarray.Dataset] = xarray_open_dataset

    def __attrs_post_init__(self):
        """raise deprecation warning."""
        warnings.warn(
            "VariablesExtension extension is deprecated and will be removed in next titiler version",
            DeprecationWarning,
            stacklevel=1,
        )

    def register(self, factory: TilerFactory):
        """Register endpoint to the tiler factory."""

        @factory.router.get(
            "/variables",
            response_model=List[str],
            responses={200: {"description": "Return Xarray Dataset variables."}},
        )
        def variables(
            src_path=Depends(factory.path_dependency),
            io_params=Depends(self.io_dependency),
        ):
            """return available variables."""
            with self.dataset_opener(src_path, **io_params.as_dict()) as ds:
                return list(ds.data_vars)  # type: ignore


@define
class DatasetMetadataExtension(FactoryExtension):
    """Add dataset metadata endpoints to a Xarray TilerFactory."""

    io_dependency: Type[DefaultDependency] = XarrayIOParams
    dataset_opener: Callable[..., xarray.Dataset] = xarray_open_dataset

    def register(self, factory: TilerFactory):  # noqa: C901
        """Register endpoint to the tiler factory."""

        @factory.router.get(
            "/dataset/",
            responses={
                200: {
                    "description": "Returns the HTML representation of the Xarray Dataset.",
                    "content": {
                        MediaType.html.value: {},
                    },
                },
            },
            response_class=HTMLResponse,
        )
        def dataset_metadata_html(
            src_path=Depends(factory.path_dependency),
            io_params=Depends(self.io_dependency),
        ):
            """Returns the HTML representation of the Xarray Dataset."""
            with self.dataset_opener(src_path, **io_params.as_dict()) as ds:
                return HTMLResponse(ds._repr_html_())

        @factory.router.get(
            "/dataset/dict",
            responses={
                200: {"description": "Returns the full Xarray dataset as a dictionary."}
            },
        )
        def dataset_metadata_dict(
            src_path=Depends(factory.path_dependency),
            io_params=Depends(self.io_dependency),
        ):
            """Returns the full Xarray dataset as a dictionary."""
            with self.dataset_opener(src_path, **io_params.as_dict()) as ds:
                return ds.to_dict(data=False)

        @factory.router.get(
            "/dataset/keys",
            response_model=List[str],
            responses={
                200: {
                    "description": "Returns the list of keys/variables in the Dataset."
                }
            },
        )
        def dataset_variables(
            src_path=Depends(factory.path_dependency),
            io_params=Depends(self.io_dependency),
        ):
            """Returns the list of keys/variables in the Dataset."""
            with self.dataset_opener(src_path, **io_params.as_dict()) as ds:
                return list(ds.data_vars)

        @factory.router.get(
            "/validate",
            responses={
                200: {
                    "content": {
                        "application/json": {},
                    },
                },
            },
        )
        def validate_dataset(  # noqa: C901
            src_path=Depends(factory.path_dependency),
            io_params=Depends(self.io_dependency),
            variable: Annotated[
                Optional[str], Query(description="Xarray Variable name.")
            ] = None,
        ):
            """Returns the HTML representation of the Xarray Dataset."""
            errors = []

            with self.dataset_opener(src_path, **io_params.as_dict()) as dst:
                variables = list(dst.data_vars)

                if variable:
                    dst = dst[variable]

                if "x" not in dst.dims and "y" not in dst.dims:
                    try:
                        latitude_var_name = next(
                            name
                            for name in ["lat", "latitude", "LAT", "LATITUDE", "Lat"]
                            if name in dst.dims
                        )
                        longitude_var_name = next(
                            name
                            for name in ["lon", "longitude", "LON", "LONGITUDE", "Lon"]
                            if name in dst.dims
                        )

                        dst = dst.rename(
                            {latitude_var_name: "y", longitude_var_name: "x"}
                        )

                        if extra_dims := [d for d in dst.dims if d not in ["x", "y"]]:
                            dst = dst.transpose(*extra_dims, "y", "x")
                        else:
                            dst = dst.transpose("y", "x")

                    except StopIteration:
                        errors.append(
                            "Dataset does not have compatible spatial coordinates"
                        )

                bounds = dst.rio.bounds()
                if not bounds:
                    errors.append("Dataset does not have rioxarray bounds")

                res = dst.rio.resolution()
                if not res:
                    errors.append("Dataset does not have rioxarray resolution")

                if res and bounds:
                    crs = dst.rio.crs or "epsg:4326"
                    xres, yres = map(abs, res)

                    # Adjust the longitude coordinates to the -180 to 180 range
                    if crs == "epsg:4326" and (dst.x > 180 + xres / 2).any():
                        dst = dst.assign_coords(x=(dst.x + 180) % 360 - 180)

                        # Sort the dataset by the updated longitude coordinates
                        dst = dst.sortby(dst.x)

                    bounds = tuple(dst.rio.bounds())
                    if crs == WGS84_CRS and (
                        bounds[0] + xres / 2 < -180
                        or bounds[1] + yres / 2 < -90
                        or bounds[2] - xres / 2 > 180
                        or bounds[3] - yres / 2 > 90
                    ):
                        errors.append(
                            "Dataset bounds are not valid, must be in [-180, 180] and [-90, 90]"
                        )

                if not dst.rio.transform():
                    errors.append("Dataset does not have rioxarray transform")

            return {
                "compatible_with_titiler": True if not errors else False,
                "errors": errors,
                "dataset_vars": variables,
            }
