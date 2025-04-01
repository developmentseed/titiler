"""titiler.xarray Extensions."""

from typing import Any, Callable, Dict, List, Type

import xarray
from attrs import define
from fastapi import Depends
from starlette.responses import HTMLResponse

from titiler.core.dependencies import DefaultDependency
from titiler.core.factory import FactoryExtension
from titiler.xarray.dependencies import XarrayIOParams
from titiler.xarray.factory import TilerFactory
from titiler.xarray.io import xarray_open_dataset


@define
class VariablesExtension(FactoryExtension):
    """Add /variables endpoint to a Xarray TilerFactory."""

    # Custom dependency for /variables
    io_dependency: Type[DefaultDependency] = XarrayIOParams
    dataset_opener: Callable[..., xarray.Dataset] = xarray_open_dataset

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
            "/keys",
            response_model=List[str],
            responses={200: {"description": "Return Xarray Dataset variables."}},
        )
        def dataset_variables(
            src_path=Depends(factory.path_dependency),
            io_params=Depends(self.io_dependency),
        ):
            """return available variables."""
            with self.dataset_opener(src_path, **io_params.as_dict()) as ds:
                return list(ds.data_vars)

        @factory.router.get(
            "/dict",
            response_model=Dict[str, Any],
            responses={200: {"description": "Return Xarray Dataset metadata as Dict."}},
        )
        def dataset_to_dict(
            src_path=Depends(factory.path_dependency),
            io_params=Depends(self.io_dependency),
        ):
            """return dataset as dict."""
            with self.dataset_opener(src_path, **io_params.as_dict()) as ds:
                return ds.to_dict(data=False)

        @factory.router.get(
            "/html",
            response_class=HTMLResponse,
            responses={
                200: {"description": "Return Xarray Dataset metadata as HTML Document."}
            },
        )
        def dataset_to_HTML(
            src_path=Depends(factory.path_dependency),
            io_params=Depends(self.io_dependency),
        ):
            """return dataset as HTML."""
            with self.dataset_opener(src_path, **io_params.as_dict()) as ds:
                return ds._repr_html_()
