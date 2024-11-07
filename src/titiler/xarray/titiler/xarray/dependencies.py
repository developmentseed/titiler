"""titiler.xarray dependencies."""

from dataclasses import dataclass
from typing import Optional, Union

import numpy
from fastapi import Query
from rio_tiler.types import RIOResampling, WarpResampling
from typing_extensions import Annotated

from titiler.core.dependencies import DefaultDependency


@dataclass
class XarrayIOParams(DefaultDependency):
    """Dataset IO Options."""

    group: Annotated[
        Optional[str],
        Query(
            description="Select a specific zarr group from a zarr hierarchy. Could be associated with a zoom level or dataset."
        ),
    ] = None

    decode_times: Annotated[
        Optional[bool],
        Query(
            title="decode_times",
            description="Whether to decode times",
        ),
    ] = None

    # cache_client


@dataclass
class XarrayDsParams(DefaultDependency):
    """Xarray Dataset Options."""

    variable: Annotated[str, Query(description="Xarray Variable name")]

    drop_dim: Annotated[
        Optional[str],
        Query(description="Dimension to drop"),
    ] = None

    datetime: Annotated[
        Optional[str], Query(description="Slice of time to read (if available)")
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

    variable: Annotated[Optional[str], Query(description="Xarray Variable name")] = None

    drop_dim: Annotated[
        Optional[str],
        Query(description="Dimension to drop"),
    ] = None

    datetime: Annotated[
        Optional[str], Query(description="Slice of time to read (if available)")
    ] = None


@dataclass
class DatasetParams(DefaultDependency):
    """Low level WarpedVRT Optional parameters."""

    nodata: Annotated[
        Optional[Union[str, int, float]],
        Query(
            title="Nodata value",
            description="Overwrite internal Nodata value",
        ),
    ] = None
    reproject_method: Annotated[
        Optional[WarpResampling],
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

    max_size: Annotated[Optional[int], "Maximum image size to read onto."] = None
    height: Annotated[Optional[int], "Force output image height."] = None
    width: Annotated[Optional[int], "Force output image width."] = None
    resampling_method: Annotated[
        Optional[RIOResampling],
        Query(
            alias="resampling",
            description="RasterIO resampling algorithm. Defaults to `nearest`.",
        ),
    ] = None

    def __post_init__(self):
        """Post Init."""
        if self.width and self.height:
            self.max_size = None
