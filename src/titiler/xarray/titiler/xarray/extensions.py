"""titiler.xarray Extensions."""

import warnings
from typing import Annotated, Any, Callable, Dict, List, Optional, Type

import xarray
from attrs import define
from fastapi import Depends
from starlette.responses import HTMLResponse

from titiler.core.dependencies import DefaultDependency
from titiler.core.factory import FactoryExtension
from titiler.core.resources.enums import MediaType
from titiler.xarray.dependencies import MetadataOutputType, XarrayIOParams
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
            "/dataset/keys",
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
            "/dataset/info",
            responses={
                200: {
                    "description": "Return Xarray Dataset metadata.",
                    "content": {
                        MediaType.json.value: {},
                        MediaType.html.value: {},
                    },
                },
            },
            response_model=Dict[str, Any],
        )
        def dataset_metadata(
            src_path=Depends(factory.path_dependency),
            io_params=Depends(self.io_dependency),
            output_type: Annotated[
                Optional[MediaType],
                Depends(MetadataOutputType),
            ] = None,
        ):
            """return dataset as dict."""
            with self.dataset_opener(src_path, **io_params.as_dict()) as ds:
                if output_type == MediaType.html:
                    return HTMLResponse(ds._repr_html_())

                return ds.to_dict(data=False)
