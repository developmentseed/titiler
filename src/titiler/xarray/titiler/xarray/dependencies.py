"""titiler.xarray dependencies."""

from dataclasses import dataclass
from typing import Optional, Union

import numpy
from fastapi import Query
from rio_tiler.types import RIOResampling, WarpResampling
from starlette.requests import Request
from typing_extensions import Annotated

from titiler.core.dependencies import DefaultDependency


@dataclass
class XarrayIOParams(DefaultDependency):
    """Dataset IO Options."""

    group: Annotated[
        Optional[int],
        Query(
            description="Select a specific zarr group from a zarr hierarchy. Could be associated with a zoom level or dataset."
        ),
    ] = None

    reference: Annotated[
        Optional[bool],
        Query(
            title="reference",
            description="Whether the dataset is a kerchunk reference",
        ),
    ] = None

    decode_times: Annotated[
        Optional[bool],
        Query(
            title="decode_times",
            description="Whether to decode times",
        ),
    ] = None

    consolidated: Annotated[
        Optional[bool],
        Query(
            title="consolidated",
            description="Whether to expect and open zarr store with consolidated metadata",
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


@dataclass(init=False)
class CompatXarrayParams(DefaultDependency):
    """Custom XarrayParams endpoints.

    This Dependency aims to be used in a tiler where both GDAL/Xarray dataset would be supported.
    By default `variable` won't be required but when using an Xarray dataset,
    it would fail without the variable query-parameter set.
    """

    # File IO Options
    group: Optional[int] = None
    reference: Optional[bool] = None
    decode_times: Optional[bool] = None
    consolidated: Optional[bool] = None

    # Dataset Options
    variable: Optional[str] = None
    drop_dim: Optional[str] = None
    datetime: Optional[str] = None

    def __init__(
        self,
        request: Request,
        variable: Annotated[
            Optional[str], Query(description="Xarray Variable name")
        ] = None,
        group: Annotated[
            Optional[int],
            Query(
                description="Select a specific zarr group from a zarr hierarchy. Could be associated with a zoom level or dataset."
            ),
        ] = None,
        reference: Annotated[
            Optional[bool],
            Query(
                title="reference",
                description="Whether the dataset is a kerchunk reference",
            ),
        ] = None,
        decode_times: Annotated[
            Optional[bool],
            Query(
                title="decode_times",
                description="Whether to decode times",
            ),
        ] = None,
        consolidated: Annotated[
            Optional[bool],
            Query(
                title="consolidated",
                description="Whether to expect and open zarr store with consolidated metadata",
            ),
        ] = None,
        drop_dim: Annotated[
            Optional[str],
            Query(description="Dimension to drop"),
        ] = None,
        datetime: Annotated[
            Optional[str], Query(description="Slice of time to read (if available)")
        ] = None,
    ):
        """Initialize XarrayIOParamsTiles

        Note: Because we don't want `z and multi-scale` to appear in the documentation we use a dataclass with a custom `__init__` method.
        FastAPI will use the `__init__` method but will exclude Request in the documentation making `pool` an invisible dependency.
        """
        self.variable = variable
        self.group = group
        self.reference = reference
        self.decode_times = decode_times
        self.consolidated = consolidated
        self.drop_dim = drop_dim
        self.datetime = datetime

        if request.query_params.get("multiscale") and request.path_params.get("z"):
            self.group = int(request.path_params.get("z"))


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


@dataclass
class TileParams(DefaultDependency):
    """Custom TileParams for Xarray."""

    multiscale: Annotated[
        Optional[bool],
        Query(
            title="multiscale",
            description="Whether the dataset has multiscale groups (Zoom levels)",
        ),
    ] = None


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
