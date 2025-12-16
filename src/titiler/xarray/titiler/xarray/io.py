"""titiler.xarray.io"""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from functools import cache
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

import attr
import httpx
import obstore
import xarray
import zarr
from morecantile import TileMatrixSet
from rio_tiler.constants import WEB_MERCATOR_TMS
from rio_tiler.io.xarray import XarrayReader
from typing_extensions import TypedDict
from zarr.storage import ObjectStore

X_DIM_NAMES = ["lon", "longitude", "LON", "LONGITUDE", "Lon", "Longitude"]
Y_DIM_NAMES = ["lat", "latitude", "LAT", "LATITUDE", "Lat", "Latitude"]


def _find_bucket_region(bucket: str, use_https: bool = True) -> str | None:
    prefix = "https" if use_https else "http"
    response = httpx.get(f"{prefix}://{bucket}.s3.amazonaws.com")
    return response.headers.get("x-amz-bucket-region")


@cache
def open_zarr(  # noqa: C901
    src_path: str,
    group: str | None = None,
    decode_times: bool = True,
    decode_coords: str = "all",
    infer_region: bool = True,
    **kwargs: Any,
) -> xarray.Dataset:
    """Open Xarray dataset with fsspec.

    Args:
        src_path (str): dataset path.
        group (Optional, str): path to the netCDF/Zarr group in the given file to open given as a str.
        decode_times (bool):  If True, decode times encoded in the standard NetCDF datetime format into datetime objects. Otherwise, leave them encoded as numbers.

    Returns:
        xarray.Dataset

    """
    parsed = urlparse(src_path)
    if not parsed.scheme:
        src_path = str(Path(src_path).resolve())
        src_path = "file://" + src_path

    # Arguments for xarray.open_dataset
    # Default args
    xr_open_args: dict[str, Any] = {
        "engine": "zarr",
        "decode_coords": decode_coords,
        "decode_times": decode_times,
    }

    # Argument if we're opening a datatree
    if group is not None:
        xr_open_args["group"] = group

    config = {**kwargs}
    # We can't expect the users to pass a REGION so we guess it
    if parsed.scheme == "s3" or "amazonaws.com" in parsed.netloc:
        if "region" not in config and infer_region:
            region_name_env = (
                os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION"))
                or None
            )

            # s3:// urls
            if parsed.scheme == "s3":
                config["region"] = _find_bucket_region(parsed.netloc) or region_name_env

            # https://{bucket}.s3.{region}?.amazonaws.com urls
            else:
                # We assume that https:// url are public object
                config["skip_signature"] = True

                # Get Region from URL or guess if needed
                if expr := re.compile(
                    r"(?P<bucket>[a-z0-9\.\-_]+)\.s3"
                    r"(\.dualstack)?"
                    r"(\.(?P<region>[a-z0-9\-_]+))?"
                    r"\.amazonaws\.(com|cn)",
                    re.IGNORECASE,
                ).match(parsed.netloc):
                    bucket = expr.groupdict()["bucket"]
                    if not expr.groupdict().get("region"):
                        config["region"] = (
                            _find_bucket_region(bucket) or region_name_env
                        )

    store = obstore.store.from_url(src_path, config=config)  # type: ignore
    zarr_store = ObjectStore(store=store, read_only=True)
    ds = xarray.open_dataset(zarr_store, **xr_open_args)  # type: ignore [arg-type]

    return ds


def _arrange_dims(da: xarray.DataArray) -> xarray.DataArray:
    """Arrange coordinates and time dimensions.

    An rioxarray.exceptions.InvalidDimensionOrder error is raised if the coordinates are not in the correct order time, y, and x.
    See: https://github.com/corteva/rioxarray/discussions/674

    We conform to using x and y as the spatial dimension names..

    """
    if "x" not in da.dims and "y" not in da.dims:
        try:
            y_dim = next(name for name in Y_DIM_NAMES if name in da.dims)
            x_dim = next(name for name in X_DIM_NAMES if name in da.dims)
        except StopIteration as e:
            raise ValueError(
                f"Couldn't find X and Y spatial coordinates in {da.dims}"
            ) from e

        da = da.rename({y_dim: "y", x_dim: "x"})

    if extra_dims := [d for d in da.dims if d not in ["x", "y"]]:
        da = da.transpose(*extra_dims, "y", "x")
    else:
        da = da.transpose("y", "x")

    # If min/max values are stored in `valid_range` we add them in `valid_min/valid_max`
    vmin, vmax = da.attrs.get("valid_min"), da.attrs.get("valid_max")
    if "valid_range" in da.attrs and not (vmin is not None and vmax is not None):
        valid_range = da.attrs.get("valid_range")
        da.attrs.update({"valid_min": valid_range[0], "valid_max": valid_range[1]})  # type: ignore

    return da


class selector(TypedDict):
    """STAC Item."""

    dimension: str
    values: list[Any]
    method: Literal["nearest", "pad", "ffill", "backfill", "bfill"] | None


def _parse_dsl(sel: list[str] | None) -> list[selector]:
    """Parse sel DSL into dictionary.

    Args:
        sel (list of str, optional): List of Xarray Indexes.

    Returns:
        list: list of dimension/values/method.

    """
    sel = sel or []

    _idx: dict[str, list] = {}
    for s in sel:
        val: str | slice
        dim, val = s.split("=")

        if dim in _idx:
            _idx[dim].append(val)
        else:
            _idx[dim] = [val]

    # Loop through all dimension=values selectors
    # - parse method::value if provided
    # - check if multiple methods are provided for the same dimension
    # - cast values to the dimension dtype
    # - apply the selection
    selectors: list[selector] = []
    for dimension, values in _idx.items():
        methods, values = zip(  # type: ignore
            *[v.split("::", 1) if "::" in v else (None, v) for v in values]
        )
        method_sets = {m for m in methods if m is not None}
        if len(method_sets) > 1:
            raise ValueError(
                f"Multiple selection methods provided for dimension {dimension}: {methods}"
            )
        method = method_sets.pop() if method_sets else None

        selectors.append(
            {
                "dimension": dimension,
                "values": list(values),
                "method": method,
            }
        )

    return selectors


def get_variable(
    ds: xarray.Dataset,
    variable: str,
    sel: list[str] | None = None,
) -> xarray.DataArray:
    """Get Xarray variable as DataArray.

    Args:
        ds (xarray.Dataset): Xarray Dataset.
        variable (str): Variable to extract from the Dataset.
        sel (list of str, optional): List of Xarray Indexes.

    Returns:
        xarray.DataArray: 2D or 3D DataArray.

    """
    da = ds[variable]

    for selector in _parse_dsl(sel):
        dimension = selector["dimension"]
        values = selector["values"]
        method = selector["method"]

        # TODO: add more casting
        # cast string to dtype of the dimension
        if da[dimension].dtype != "O":
            values = [da[dimension].dtype.type(v) for v in values]

        da = da.sel(
            {dimension: values[0] if len(values) < 2 else values},
            method=method,
        )

    da = _arrange_dims(da)

    # Make sure we have a valid CRS
    crs = da.rio.crs or "epsg:4326"
    da = da.rio.write_crs(crs)

    if crs == "epsg:4326" and (da.x > 180).any():
        # Adjust the longitude coordinates to the -180 to 180 range
        da = da.assign_coords(x=(da.x + 180) % 360 - 180)

        # Sort the dataset by the updated longitude coordinates
        da = da.sortby(da.x)

    assert len(da.dims) in [2, 3], "titiler.xarray can only work with 2D or 3D dataset"

    return da


@attr.s
class Reader(XarrayReader):
    """Reader: Open Zarr file and access DataArray."""

    src_path: str = attr.ib()
    variable: str = attr.ib()

    # xarray.Dataset options
    opener: Callable[..., xarray.Dataset] = attr.ib(default=open_zarr)
    opener_options: dict = attr.ib(factory=dict)

    group: str | None = attr.ib(default=None)
    decode_times: bool = attr.ib(default=True)

    # xarray.DataArray options
    sel: list[str] | None = attr.ib(default=None)
    method: Literal["nearest", "pad", "ffill", "backfill", "bfill"] | None = attr.ib(
        default=None
    )

    tms: TileMatrixSet = attr.ib(default=WEB_MERCATOR_TMS)

    ds: xarray.Dataset = attr.ib(init=False)
    input: xarray.DataArray = attr.ib(init=False)

    _dims: list = attr.ib(init=False, factory=list)

    def __attrs_post_init__(self):
        """Set bounds and CRS."""
        opener_options = {
            "group": self.group,
            "decode_times": self.decode_times,
            **self.opener_options,
        }

        self.ds = self.opener(self.src_path, **opener_options)
        self.input = get_variable(
            self.ds,
            self.variable,
            sel=self.sel,
        )
        super().__attrs_post_init__()

    def close(self):
        """Close xarray dataset."""
        self.ds.close()

    def __exit__(self, exc_type, exc_value, traceback):
        """Support using with Context Managers."""
        self.close()


def fs_open_dataset(  # noqa: C901
    src_path: str,
    group: str | None = None,
    decode_times: bool = True,
    decode_coords: str = "all",
    **kwargs,
) -> xarray.Dataset:
    """Open Xarray dataset with fsspec.

    Args:
        src_path (str): dataset path.
        group (Optional, str): path to the netCDF/Zarr group in the given file to open given as a str.
        decode_times (bool):  If True, decode times encoded in the standard NetCDF datetime format into datetime objects. Otherwise, leave them encoded as numbers.

    Returns:
        xarray.Dataset

    """
    import fsspec  # noqa

    try:
        import h5netcdf
    except ImportError:  # pragma: nocover
        h5netcdf = None  # type: ignore

    parsed = urlparse(src_path)
    protocol = parsed.scheme or "file"

    # Arguments for xarray.open_dataset
    # Default args
    xr_open_args: dict[str, Any] = {
        "decode_coords": decode_coords,
        "decode_times": decode_times,
    }

    # Argument if we're opening a datatree
    if group is not None:
        xr_open_args["group"] = group

    # NetCDF arguments
    if any(src_path.lower().endswith(ext) for ext in [".nc", ".nc4"]):
        assert (
            h5netcdf is not None
        ), "'h5netcdf' must be installed to read NetCDF dataset"

        xr_open_args.update(
            {
                "engine": "h5netcdf",
                "lock": False,
            }
        )
        fs = fsspec.filesystem(protocol, **kwargs)
        ds = xarray.open_dataset(fs.open(src_path), **xr_open_args)

    # Fallback to Zarr
    else:
        store = zarr.storage.FsspecStore.from_url(
            src_path, storage_options={"asynchronous": True, **kwargs}
        )
        ds = xarray.open_zarr(store, **xr_open_args)

    return ds


# Compat
xarray_open_dataset = fs_open_dataset


@attr.s
class FsReader(Reader):
    """Reader with fs_open_dataset opener"""

    opener: Callable[..., xarray.Dataset] = attr.ib(default=fs_open_dataset)
