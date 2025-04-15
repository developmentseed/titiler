"""titiler.xarray Extensions."""

import warnings
from typing import Callable, List, Type

import xarray
from attrs import define
from fastapi import Depends
from starlette.responses import HTMLResponse

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

    def register(self, factory: TilerFactory):
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
