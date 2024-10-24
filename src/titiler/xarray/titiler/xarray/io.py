"""titiler.xarray.io"""

import pickle
import re
from typing import Any, Callable, Dict, List, Optional, Protocol

import attr
import fsspec
import numpy
import s3fs
import xarray
from morecantile import TileMatrixSet
from rio_tiler.constants import WEB_MERCATOR_TMS
from rio_tiler.io.xarray import XarrayReader


class CacheClient(Protocol):
    """CacheClient Protocol."""

    def get(self, key: str) -> bytes:
        """Get key."""
        ...

    def set(self, key: str, body: bytes) -> None:
        """Set key."""
        ...


def parse_protocol(src_path: str, reference: Optional[bool] = False) -> str:
    """Parse protocol from path."""
    match = re.match(r"^(s3|https|http)", src_path)
    protocol = "file"
    if match:
        protocol = match.group(0)

    # override protocol if reference
    if reference:
        protocol = "reference"

    return protocol


def xarray_engine(src_path: str) -> str:
    """Parse xarray engine from path."""
    #  ".hdf", ".hdf5", ".h5" will be supported once we have tests + expand the type permitted for the group parameter
    if any(src_path.lower().endswith(ext) for ext in [".nc", ".nc4"]):
        return "h5netcdf"
    else:
        return "zarr"


def get_filesystem(
    src_path: str,
    protocol: str,
    xr_engine: str,
    anon: bool = True,
):
    """
    Get the filesystem for the given source path.
    """
    if protocol == "s3":
        s3_filesystem = s3fs.S3FileSystem()
        return (
            s3_filesystem.open(src_path)
            if xr_engine == "h5netcdf"
            else s3fs.S3Map(root=src_path, s3=s3_filesystem)
        )

    elif protocol == "reference":
        reference_args = {"fo": src_path, "remote_options": {"anon": anon}}
        return fsspec.filesystem("reference", **reference_args).get_mapper("")

    elif protocol in ["https", "http", "file"]:
        filesystem = fsspec.filesystem(protocol)  # type: ignore
        return (
            filesystem.open(src_path)
            if xr_engine == "h5netcdf"
            else filesystem.get_mapper(src_path)
        )

    else:
        raise ValueError(f"Unsupported protocol: {protocol}")


def xarray_open_dataset(
    src_path: str,
    group: Optional[Any] = None,
    reference: Optional[bool] = False,
    decode_times: Optional[bool] = True,
    consolidated: Optional[bool] = True,
    cache_client: Optional[CacheClient] = None,
) -> xarray.Dataset:
    """Open dataset."""
    # Generate cache key and attempt to fetch the dataset from cache
    if cache_client:
        cache_key = f"{src_path}_{group}" if group is not None else src_path
        data_bytes = cache_client.get(cache_key)
        if data_bytes:
            return pickle.loads(data_bytes)

    protocol = parse_protocol(src_path, reference=reference)
    xr_engine = xarray_engine(src_path)
    file_handler = get_filesystem(src_path, protocol, xr_engine)

    # Arguments for xarray.open_dataset
    # Default args
    xr_open_args: Dict[str, Any] = {
        "decode_coords": "all",
        "decode_times": decode_times,
    }

    # Argument if we're opening a datatree
    if isinstance(group, int):
        xr_open_args["group"] = group

    # NetCDF arguments
    if xr_engine == "h5netcdf":
        xr_open_args["engine"] = "h5netcdf"
        xr_open_args["lock"] = False
    else:
        # Zarr arguments
        xr_open_args["engine"] = "zarr"
        xr_open_args["consolidated"] = consolidated

    # Additional arguments when dealing with a reference file.
    if reference:
        xr_open_args["consolidated"] = False
        xr_open_args["backend_kwargs"] = {"consolidated": False}

    ds = xarray.open_dataset(file_handler, **xr_open_args)

    if cache_client:
        # Serialize the dataset to bytes using pickle
        data_bytes = pickle.dumps(ds)
        cache_client.set(cache_key, data_bytes)

    return ds


def arrange_coordinates(da: xarray.DataArray) -> xarray.DataArray:
    """Arrange coordinates to DataArray.

    An rioxarray.exceptions.InvalidDimensionOrder error is raised if the coordinates are not in the correct order time, y, and x.
    See: https://github.com/corteva/rioxarray/discussions/674

    We conform to using x and y as the spatial dimension names. You can do this a bit more elegantly with metpy but that is a heavy dependency.

    """
    if "x" not in da.dims and "y" not in da.dims:
        latitude_var_name = "latitude" if "latitude" in da.dims else "lat"
        longitude_var_name = "longitude" if "longitude" in da.dims else "lon"
        da = da.rename({latitude_var_name: "y", longitude_var_name: "x"})

    if "time" in da.dims:
        da = da.transpose("time", "y", "x")
    else:
        da = da.transpose("y", "x")

    return da


def get_variable(
    ds: xarray.Dataset,
    variable: str,
    datetime: Optional[str] = None,
    drop_dim: Optional[str] = None,
) -> xarray.DataArray:
    """Get Xarray variable as DataArray."""
    da = ds[variable]
    da = arrange_coordinates(da)  # TODO: Duplicated call L173

    # TODO: add test
    if drop_dim:
        dim_to_drop, dim_val = drop_dim.split("=")
        da = da.sel({dim_to_drop: dim_val}).drop(dim_to_drop)

    da = arrange_coordinates(da)

    # Make sure we have a valid CRS
    crs = da.rio.crs or "epsg:4326"
    da = da.rio.write_crs(crs)

    if crs == "epsg:4326" and (da.x > 180).any():
        # Adjust the longitude coordinates to the -180 to 180 range
        da = da.assign_coords(x=(da.x + 180) % 360 - 180)

        # Sort the dataset by the updated longitude coordinates
        da = da.sortby(da.x)

    if "time" in da.dims:
        if datetime:
            time_as_str = datetime.split("T")[0]
            if da["time"].dtype == "O":
                da["time"] = da["time"].astype("datetime64[ns]")
            da = da.sel(
                time=numpy.array(time_as_str, dtype=numpy.datetime64), method="nearest"
            )
        else:
            da = da.isel(time=0)

    return da


@attr.s
class Reader(XarrayReader):
    """Reader: Open Zarr file and access DataArray."""

    src_path: str = attr.ib()
    variable: str = attr.ib()

    # xarray.Dataset options
    opener: Callable[..., xarray.Dataset] = attr.ib(default=xarray_open_dataset)

    group: Optional[Any] = attr.ib(default=None)
    reference: bool = attr.ib(default=False)
    decode_times: bool = attr.ib(default=False)
    consolidated: Optional[bool] = attr.ib(default=True)
    cache_client: Optional[CacheClient] = attr.ib(default=None)

    # xarray.DataArray options
    datetime: Optional[str] = attr.ib(default=None)
    drop_dim: Optional[str] = attr.ib(default=None)

    tms: TileMatrixSet = attr.ib(default=WEB_MERCATOR_TMS)

    ds: xarray.Dataset = attr.ib(init=False)
    input: xarray.DataArray = attr.ib(init=False)

    _dims: List = attr.ib(init=False, factory=list)

    def __attrs_post_init__(self):
        """Set bounds and CRS."""
        self.ds = self.opener(
            self.src_path,
            group=self.group,
            reference=self.reference,
            decode_times=self.decode_times,
            consolidated=self.consolidated,
            cache_client=self.cache_client,
        )

        self.input = get_variable(
            self.ds,
            self.variable,
            datetime=self.datetime,
            drop_dim=self.drop_dim,
        )
        super().__attrs_post_init__()

    def close(self):
        """Close xarray dataset."""
        self.ds.close()

    def __exit__(self, exc_type, exc_value, traceback):
        """Support using with Context Managers."""
        self.close()

    @classmethod
    def list_variables(
        cls,
        src_path: str,
        group: Optional[Any] = None,
        reference: Optional[bool] = False,
        consolidated: Optional[bool] = True,
    ) -> List[str]:
        """List available variable in a dataset."""
        with xarray_open_dataset(
            src_path,
            group=group,
            reference=reference,
            consolidated=consolidated,
        ) as ds:
            return list(ds.data_vars)  # type: ignore
