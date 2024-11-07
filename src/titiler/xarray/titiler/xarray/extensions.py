"""titiler.xarray Extensions."""

from typing import Callable, List, Type

import xarray
from attrs import define
from fastapi import Depends

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
