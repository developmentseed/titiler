"""titiler.xarray.io"""

from typing import Any, Callable, Dict, List, Literal, Optional, Union
from urllib.parse import urlparse

import attr
import numpy
import pandas
import xarray
from morecantile import TileMatrixSet
from rio_tiler.constants import WEB_MERCATOR_TMS
from rio_tiler.io.xarray import XarrayReader
from xarray.namedarray.utils import module_available


def xarray_open_dataset(  # noqa: C901
    src_path: str,
    group: Optional[str] = None,
    decode_times: bool = True,
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

    try:
        import zarr
    except ImportError:  # pragma: nocover
        zarr = None  # type: ignore

    parsed = urlparse(src_path)
    protocol = parsed.scheme or "file"

    if any(src_path.lower().endswith(ext) for ext in [".nc", ".nc4"]):
        assert (
            h5netcdf is not None
        ), "'h5netcdf' must be installed to read NetCDF dataset"

        xr_engine = "h5netcdf"

    else:
        assert zarr is not None, "'zarr' must be installed to read Zarr dataset"
        xr_engine = "zarr"

    # Arguments for xarray.open_dataset
    # Default args
    xr_open_args: Dict[str, Any] = {
        "decode_coords": "all",
        "decode_times": decode_times,
    }

    # Argument if we're opening a datatree
    if group is not None:
        xr_open_args["group"] = group

    # NetCDF arguments
    if xr_engine == "h5netcdf":
        xr_open_args.update(
            {
                "engine": "h5netcdf",
                "lock": False,
            }
        )
        fs = fsspec.filesystem(protocol)
        ds = xarray.open_dataset(fs.open(src_path), **xr_open_args)

    # Fallback to Zarr
    else:
        if module_available("zarr", minversion="3.0"):
            if protocol == "file":
                store = zarr.storage.LocalStore(parsed.path, read_only=True)
            else:
                fs = fsspec.filesystem(protocol, storage_options={"asynchronous": True})
                store = zarr.storage.FsspecStore(fs, path=src_path, read_only=True)

        else:
            store = fsspec.filesystem(protocol).get_mapper(src_path)

        ds = xarray.open_zarr(store, **xr_open_args)
    return ds


def _arrange_dims(da: xarray.DataArray) -> xarray.DataArray:
    """Arrange coordinates and time dimensions.

    An rioxarray.exceptions.InvalidDimensionOrder error is raised if the coordinates are not in the correct order time, y, and x.
    See: https://github.com/corteva/rioxarray/discussions/674

    We conform to using x and y as the spatial dimension names..

    """
    if "x" not in da.dims and "y" not in da.dims:
        try:
            latitude_var_name = next(
                name
                for name in ["lat", "latitude", "LAT", "LATITUDE", "Lat"]
                if name in da.dims
            )
            longitude_var_name = next(
                name
                for name in ["lon", "longitude", "LON", "LONGITUDE", "Lon"]
                if name in da.dims
            )
        except StopIteration as e:
            raise ValueError(f"Couldn't find X/Y dimensions in {da.dims}") from e

        da = da.rename({latitude_var_name: "y", longitude_var_name: "x"})

    if "TIME" in da.dims:
        da = da.rename({"TIME": "time"})

    if extra_dims := [d for d in da.dims if d not in ["x", "y"]]:
        da = da.transpose(*extra_dims, "y", "x")
    else:
        da = da.transpose("y", "x")

    # If min/max values are stored in `valid_range` we add them in `valid_min/valid_max`
    vmin, vmax = da.attrs.get("valid_min"), da.attrs.get("valid_max")
    if "valid_range" in da.attrs and not (vmin is not None and vmax is not None):
        valid_range = da.attrs.get("valid_range")
        da.attrs.update({"valid_min": valid_range[0], "valid_max": valid_range[1]})

    return da


def _cast_to_type(value, dtype: Any) -> Any:
    if "timedelta" in str(dtype):
        value = pandas.to_timedelta(value)

    elif numpy.issubdtype(dtype, numpy.integer):
        value = int(value)

    elif numpy.issubdtype(dtype, numpy.floating):
        value = float(value)

    return value


def get_variable(
    ds: xarray.Dataset,
    variable: str,
    sel: Optional[List[str]] = None,
    method: Optional[Literal["nearest", "pad", "ffill", "backfill", "bfill"]] = None,
) -> xarray.DataArray:
    """Get Xarray variable as DataArray.

    Args:
        ds (xarray.Dataset): Xarray Dataset.
        variable (str): Variable to extract from the Dataset.
        sel (list of str, optional): List of Xarray Indexes.
        method (str): Xarray indexing method.

    Returns:
        xarray.DataArray: 2D or 3D DataArray.

    """
    da = ds[variable]

    if sel:
        _idx: Dict[str, List] = {}
        for s in sel:
            val: Union[str, slice]
            dim, val = s.split("=")
            val = _cast_to_type(val, da[dim].dtype)

            if dim in _idx:
                _idx[dim].append(val)
            else:
                _idx[dim] = [val]

        sel_idx = {k: v[0] if len(v) < 2 else v for k, v in _idx.items()}
        da = da.sel(sel_idx, method=method)

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
    opener: Callable[..., xarray.Dataset] = attr.ib(default=xarray_open_dataset)

    group: Optional[str] = attr.ib(default=None)
    decode_times: bool = attr.ib(default=True)

    # xarray.DataArray options
    sel: Optional[List[str]] = attr.ib(default=None)
    method: Optional[Literal["nearest", "pad", "ffill", "backfill", "bfill"]] = attr.ib(
        default=None
    )

    tms: TileMatrixSet = attr.ib(default=WEB_MERCATOR_TMS)

    ds: xarray.Dataset = attr.ib(init=False)
    input: xarray.DataArray = attr.ib(init=False)

    _dims: List = attr.ib(init=False, factory=list)

    def __attrs_post_init__(self):
        """Set bounds and CRS."""
        self.ds = self.opener(
            self.src_path,
            group=self.group,
            decode_times=self.decode_times,
        )

        self.input = get_variable(
            self.ds,
            self.variable,
            sel=self.sel,
            method=self.method,
        )
        super().__attrs_post_init__()

    def close(self):
        """Close xarray dataset."""
        self.ds.close()

    def __exit__(self, exc_type, exc_value, traceback):
        """Support using with Context Managers."""
        self.close()
