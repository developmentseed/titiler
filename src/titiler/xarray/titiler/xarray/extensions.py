"""titiler.xarray Extensions."""

import warnings
from collections.abc import Callable
from typing import Annotated

import xarray
from attrs import define
from fastapi import Depends, Query
from rio_tiler.constants import WGS84_CRS
from starlette.responses import HTMLResponse
from typing_extensions import TypedDict

from titiler.core.dependencies import DefaultDependency
from titiler.core.factory import FactoryExtension
from titiler.core.resources.enums import MediaType
from titiler.xarray.dependencies import XarrayIOParams
from titiler.xarray.factory import TilerFactory
from titiler.xarray.io import X_DIM_NAMES, Y_DIM_NAMES, open_zarr


@define
class VariablesExtension(FactoryExtension):
    """Add /variables endpoint to a Xarray TilerFactory."""

    # Custom dependency for /variables
    io_dependency: type[DefaultDependency] = XarrayIOParams
    dataset_opener: Callable[..., xarray.Dataset] = open_zarr

    def __attrs_post_init__(self):
        """raise deprecation warning."""
        warnings.warn(
            "VariablesExtension extension is deprecated and will be removed in next titiler version",
            DeprecationWarning,
            stacklevel=1,
        )

    def register(self, factory: TilerFactory):  # type: ignore [override]
        """Register endpoint to the tiler factory."""

        @factory.router.get(
            "/variables",
            response_model=list[str],
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

    io_dependency: type[DefaultDependency] = XarrayIOParams
    dataset_opener: Callable[..., xarray.Dataset] = open_zarr

    def register(self, factory: TilerFactory):  # type: ignore [override] # noqa: C901
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
            response_model=list[str],
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


class ValidationInfo(TypedDict):
    """Variable Validation model."""

    compatible_with_titiler: bool
    errors: list[str]
    warnings: list[str]


@define
class ValidateExtension(FactoryExtension):
    """Add /validate endpoints to a Xarray TilerFactory."""

    io_dependency: type[DefaultDependency] = XarrayIOParams
    dataset_opener: Callable[..., xarray.Dataset] = open_zarr

    def _validate_variable(self, da: xarray.DataArray) -> ValidationInfo:  # noqa: C901
        errors: list[str] = []
        warnings: list[str] = []

        if len(da.dims) not in [2, 3]:
            warnings.append(
                f"DataArray has too many dimension ({len(da.dims)}) for titiler.xarray, dimensions reduction (sel) will be required.",
            )

        if "y" not in da.dims:
            try:
                y_dim = next(name for name in Y_DIM_NAMES if name in da.dims)
                da = da.rename({y_dim: "y"})

            except StopIteration:
                errors.append(
                    "Dataset does not have compatible `Y` spatial coordinates"
                )

        if "x" not in da.dims:
            try:
                x_dim = next(name for name in X_DIM_NAMES if name in da.dims)
                da = da.rename({x_dim: "x"})
            except StopIteration:
                errors.append(
                    "Dataset does not have compatible `X` spatial coordinates"
                )

        if {"x", "y"}.issubset(set(da.dims)):
            if extra_dims := [d for d in da.dims if d not in ["x", "y"]]:
                da = da.transpose(*extra_dims, "y", "x")
            else:
                da = da.transpose("y", "x")

            bounds = da.rio.bounds()
            if not bounds:
                errors.append("Dataset does not have rioxarray bounds")

            res = da.rio.resolution()
            if not res:
                errors.append("Dataset does not have rioxarray resolution")

            if res and bounds:
                crs = da.rio.crs or "epsg:4326"
                xres, yres = map(abs, res)

                # Adjust the longitude coordinates to the -180 to 180 range
                if crs == "epsg:4326" and (da.x > 180 + xres / 2).any():
                    da = da.assign_coords(x=(da.x + 180) % 360 - 180)

                    # Sort the dataset by the updated longitude coordinates
                    da = da.sortby(da.x)

                bounds = tuple(da.rio.bounds())
                if crs == WGS84_CRS and (
                    bounds[0] + xres / 2 < -180
                    or bounds[1] + yres / 2 < -90
                    or bounds[2] - xres / 2 > 180
                    or bounds[3] - yres / 2 > 90
                ):
                    errors.append(
                        "Dataset bounds are not valid, must be in [-180, 180] and [-90, 90]"
                    )

            if not da.rio.transform():
                errors.append("Dataset does not have rioxarray transform")

        return {
            "compatible_with_titiler": True if not errors else False,
            "errors": errors,
            "warnings": warnings,
        }

    def register(self, factory: TilerFactory):  # type: ignore [override] # noqa: C901
        """Register endpoint to the tiler factory."""

        @factory.router.get(
            "/validate",
            responses={
                200: {
                    "content": {
                        "application/json": {},
                    },
                },
            },
            response_model=dict[str, ValidationInfo],
        )
        def validate_dataset(
            src_path=Depends(factory.path_dependency),
            io_params=Depends(self.io_dependency),
            variables: Annotated[
                list[str] | None, Query(description="Xarray Variable name.")
            ] = None,
        ):
            """Returns the HTML representation of the Xarray Dataset."""
            with self.dataset_opener(src_path, **io_params.as_dict()) as dst:
                variables = variables or list(dst.data_vars)  # type: ignore
                return {v: self._validate_variable(dst[v]) for v in variables}
