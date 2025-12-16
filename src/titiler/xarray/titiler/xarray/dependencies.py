"""titiler.xarray dependencies."""

from dataclasses import dataclass
from typing import Annotated

import numpy
from fastapi import Query
from pydantic import Field
from pydantic.types import StringConstraints
from rio_tiler.types import RIOResampling, WarpResampling

from titiler.core.dependencies import DefaultDependency


@dataclass
class XarrayIOParams(DefaultDependency):
    """Dataset IO Options."""

    group: Annotated[
        str | None,
        Query(
            description="Select a specific zarr group from a zarr hierarchy. Could be associated with a zoom level or dataset."
        ),
    ] = None

    decode_times: Annotated[
        bool | None,
        Query(
            title="decode_times",
            description="Whether to decode times",
        ),
    ] = None


SelDimStr = Annotated[
    str,
    StringConstraints(
        pattern=r"^[^=]+=((nearest|pad|ffill|backfill|bfill)::)?[^=::]+$"
    ),
]


@dataclass
class XarrayDsParams(DefaultDependency):
    """Xarray Dataset Options."""

    variable: Annotated[str, Query(description="Xarray Variable name.")]

    sel: Annotated[
        list[SelDimStr] | None,
        Query(
            description="Xarray Indexing using dimension names `{dimension}={value}` or `{dimension}={method}::{value}`.",
        ),
    ] = None


@dataclass
class XarrayParams(XarrayIOParams, XarrayDsParams):
    """Xarray Reader dependency."""

    pass


@dataclass
class CompatXarrayParams(XarrayIOParams):
    """Custom XarrayParams endpoints.

    This Dependency aims to be used in a tiler where both GDAL/Xarray dataset would be supported.
    By default `variable` won't be required but when using an Xarray dataset,
    it would fail without the variable query-parameter set.
    """

    variable: Annotated[str | None, Query(description="Xarray Variable name.")] = None

    sel: Annotated[
        list[SelDimStr] | None,
        Query(
            description="Xarray Indexing using dimension names `{dimension}={value}` or `{dimension}={method}::{value}`.",
        ),
    ] = None


@dataclass
class DatasetParams(DefaultDependency):
    """Low level WarpedVRT Optional parameters."""

    nodata: Annotated[
        str | int | float | None,
        Query(
            title="Nodata value",
            description="Overwrite internal Nodata value",
        ),
    ] = None
    reproject_method: Annotated[
        WarpResampling | None,
        Query(
            alias="reproject",
            description="WarpKernel resampling algorithm (only used when doing re-projection). Defaults to `nearest`.",
        ),
    ] = None

    def __post_init__(self):
        """Post Init."""
        if self.nodata is not None:
            self.nodata = numpy.nan if self.nodata == "nan" else float(self.nodata)


# Custom PartFeatureParams which add `resampling`
@dataclass
class PartFeatureParams(DefaultDependency):
    """Common parameters for bbox and feature."""

    max_size: Annotated[
        int | None, Field(description="Maximum image size to read onto.")
    ] = None
    height: Annotated[int | None, Field(description="Force output image height.")] = (
        None
    )
    width: Annotated[int | None, Field(description="Force output image width.")] = None
    resampling_method: Annotated[
        RIOResampling | None,
        Query(
            alias="resampling",
            description="RasterIO resampling algorithm. Defaults to `nearest`.",
        ),
    ] = None

    def __post_init__(self):
        """Post Init."""
        if self.width or self.height:
            self.max_size = None


# Custom PreviewParams which add `resampling`
@dataclass
class PreviewParams(DefaultDependency):
    """Common Preview parameters."""

    max_size: Annotated[
        int | None, Field(description="Maximum image size to read onto.")
    ] = 1024
    height: Annotated[int | None, Field(description="Force output image height.")] = (
        None
    )
    width: Annotated[int | None, Field(description="Force output image width.")] = None
    resampling_method: Annotated[
        RIOResampling | None,
        Query(
            alias="resampling",
            description="RasterIO resampling algorithm. Defaults to `nearest`.",
        ),
    ] = None

    def __post_init__(self):
        """Post Init."""
        if self.width or self.height:
            self.max_size = None

        # NOTE: By default we don't exclude None when we forward the parameter to the preview() method
        # because we need to be able to pass max_size=None
        # So we need to set the `resampling_method` to a default = 'nearest'
        # https://github.com/developmentseed/titiler/blob/b8cc304382d0cb3b4f16cea9dbb0cfba35517085/src/titiler/core/titiler/core/factory.py#L1300
        self.resampling_method = self.resampling_method or "nearest"
