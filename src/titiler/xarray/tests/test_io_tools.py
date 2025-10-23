"""test titiler.xarray.io utility functions."""

import os
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import numpy
import pytest
import xarray

from titiler.xarray.io import Reader, get_variable, xarray_open_dataset

prefix = os.path.join(os.path.dirname(__file__), "fixtures")


def test_get_variable():
    """test io.get_variable."""
    arr = numpy.arange(0, 33 * 35 * 2).reshape(2, 33, 35)
    data = xarray.DataArray(
        arr,
        dims=("time", "y", "x"),
        coords={
            "x": numpy.arange(-170, 180, 10),
            "y": numpy.arange(-80, 85, 5),
            "time": [datetime(2022, 1, 1), datetime(2023, 1, 1)],
        },
    )
    data.attrs.update({"valid_min": arr.min(), "valid_max": arr.max()})
    assert not data.rio.crs
    assert data.dims == ("time", "y", "x")

    ds = data.to_dataset(name="dataset")
    da = get_variable(ds, "dataset")
    assert da.rio.crs
    assert da.dims == ("time", "y", "x")
    assert da["time"].shape == (2,)

    da = get_variable(ds, "dataset", sel=["time=2022-01-01"])
    assert da.rio.crs
    assert da.dims == ("y", "x")
    assert da["time"] == numpy.datetime64("2022-01-01")

    da = get_variable(ds, "dataset", sel=["time=2023-01-01T00:00:00"])
    assert da.rio.crs
    assert da.dims == ("y", "x")
    assert da["time"] == numpy.datetime64("2023-01-01")

    # no time for 2022-12-01T00:00:00
    with pytest.raises(KeyError):
        get_variable(ds, "dataset", sel=["time=2022-12-01", "time=2023-01-01"])

    da = get_variable(
        ds,
        "dataset",
        sel=["time=2022-12-01", "time=2023-01-01"],
        method="nearest",
    )
    assert da.rio.crs
    assert da.dims == ("time", "y", "x")
    assert da["time"].shape == (2,)
    assert da["time"][0] == numpy.datetime64("2023-01-01")
    assert da["time"][1] == numpy.datetime64("2023-01-01")

    da = get_variable(ds, "dataset", sel=["time=2022-01-01", "time=2023-01-01"])
    assert da.rio.crs
    assert da.dims == ("time", "y", "x")
    assert da["time"].shape == (2,)
    assert da["time"][0] == numpy.datetime64("2022-01-01")
    assert da["time"][1] == numpy.datetime64("2023-01-01")

    # Select the Nearest Time
    da = get_variable(ds, "dataset", sel=["time=2024-01-01T01:00:00"], method="nearest")
    assert da.rio.crs
    assert da.dims == ("y", "x")
    assert da["time"] == numpy.datetime64("2023-01-01")

    data = data.rename({"y": "Lat", "x": "Lon"})
    assert data.dims == ("time", "Lat", "Lon")
    ds = data.to_dataset(name="dataset")
    da = get_variable(ds, "dataset")
    assert da.rio.crs
    assert da.dims == ("time", "y", "x")

    # 4D dataset
    arr = numpy.arange(0, 33 * 35 * 2).reshape(2, 1, 33, 35)
    data = xarray.DataArray(
        arr,
        dims=("time", "z", "y", "x"),
        coords={
            "x": numpy.arange(-170, 180, 10),
            "y": numpy.arange(-80, 85, 5),
            "z": [0],
            "time": [datetime(2022, 1, 1), datetime(2023, 1, 1)],
        },
    )
    ds = data.to_dataset(name="dataset")

    # We need to reduce the dim
    with pytest.raises(AssertionError):
        get_variable(ds, "dataset")

    # Reduce on Z
    da = get_variable(ds, "dataset", sel=["z=0"])
    assert da.rio.crs
    assert da.dims == ("time", "y", "x")

    # 5D dataset
    arr = numpy.arange(0, 33 * 35 * 2).reshape(2, 1, 1, 33, 35)
    data = xarray.DataArray(
        arr,
        dims=("time", "universe", "z", "y", "x"),
        coords={
            "x": numpy.arange(-170, 180, 10),
            "y": numpy.arange(-80, 85, 5),
            "z": [0],
            "universe": ["somewhere"],
            "time": [datetime(2022, 1, 1), datetime(2023, 1, 1)],
        },
    )
    ds = data.to_dataset(name="dataset")
    with pytest.raises(AssertionError):
        get_variable(ds, "dataset")

    with pytest.raises(AssertionError):
        da = get_variable(ds, "dataset", sel=["universe=somewhere"])

    da = get_variable(ds, "dataset", sel=["universe=somewhere", "time=2022-01-01"])
    assert da.rio.crs
    assert da.dims == ("z", "y", "x")

    # 5D dataset
    arr = numpy.arange(0, 33 * 35 * 2).reshape(2, 1, 1, 33, 35)
    data = xarray.DataArray(
        arr,
        dims=("time", "universe", "z", "y", "x"),
        coords={
            "x": numpy.arange(-170, 180, 10),
            "y": numpy.arange(-80, 85, 5),
            "z": [0],
            "universe": ["somewhere"],
            "time": [datetime(2022, 1, 1), datetime(2023, 1, 1)],
        },
    )

    da = get_variable(
        ds, "dataset", sel=["universe=somewhere", "time=2022-01-01T00:00:00"]
    )
    assert da.rio.crs
    assert da.dims == ("z", "y", "x")

    # 5D dataset
    arr = numpy.arange(0, 33 * 35 * 2).reshape(2, 33, 35)
    data = xarray.DataArray(
        arr,
        dims=("time", "haut_bas", "gauche_droite"),
        coords={
            "gauche_droite": numpy.arange(-170, 180, 10),
            "haut_bas": numpy.arange(-80, 85, 5),
            "time": [datetime(2022, 1, 1), datetime(2023, 1, 1)],
        },
    )

    ds = data.to_dataset(name="dataset")
    with pytest.raises(ValueError):
        da = get_variable(ds, "dataset")


def test_get_variable_datetime_tz():
    """test io.get_variable with datetime and timezones."""
    arr = numpy.arange(0, 33 * 35 * 2).reshape(2, 33, 35)
    data = xarray.DataArray(
        arr,
        dims=("time", "y", "x"),
        coords={
            "x": numpy.arange(-170, 180, 10),
            "y": numpy.arange(-80, 85, 5),
            "time": [
                datetime(2022, 1, 1),
                datetime(2023, 1, 1),
            ],
        },
    )
    data.attrs.update({"valid_min": arr.min(), "valid_max": arr.max()})
    assert not data.rio.crs
    assert data.dims == ("time", "y", "x")
    ds = data.to_dataset(name="dataset")

    da = get_variable(ds, "dataset", sel=["time=2023-01-01T00:00:00"], method="nearest")
    assert da.rio.crs
    assert da.dims == ("y", "x")
    assert da["time"] == numpy.datetime64("2023-01-01")

    da = get_variable(
        ds, "dataset", sel=["time=2023-01-01T00:00:00Z"], method="nearest"
    )
    assert da.rio.crs
    assert da.dims == ("y", "x")
    assert da["time"] == numpy.datetime64("2023-01-01")

    da = get_variable(
        ds, "dataset", sel=["time=2023-01-01T00:00:00+03:00"], method="nearest"
    )
    assert da.rio.crs
    assert da.dims == ("y", "x")
    assert da["time"] == numpy.datetime64("2023-01-01")


@pytest.mark.parametrize(
    "protocol,filename",
    [
        ("file://", "dataset_2d.nc"),
        ("file://", "dataset_3d.nc"),
        ("file://", "dataset_3d.zarr"),
        ("", "dataset_2d.nc"),
        ("", "dataset_3d.nc"),
        ("", "dataset_3d.zarr"),
    ],
)
def test_reader(protocol, filename):
    """test reader."""
    src_path = protocol + os.path.join(protocol, prefix, filename)
    with Reader(src_path, variable="dataset") as src:
        assert src.info()
        assert src.tile(0, 0, 0)


def test_opener():
    """test custom opener"""
    src_path = "file://" + os.path.join("file://", prefix, "dataset_2d.nc")

    def custom_netcdf_opener(  # noqa: C901
        src_path: str,
        special_arg: bool,
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

        parsed = urlparse(src_path)
        protocol = parsed.scheme or "file"

        if not special_arg:
            raise ValueError("you forgot the special_arg :(")

        xr_open_args: Dict[str, Any] = {
            "decode_coords": "all",
            "decode_times": decode_times,
            "engine": "h5netcdf",
            "lock": False,
        }

        # Argument if we're opening a datatree
        if group is not None:
            xr_open_args["group"] = group

        fs = fsspec.filesystem(protocol)
        ds = xarray.open_dataset(fs.open(src_path), **xr_open_args)

        return ds

    with Reader(
        src_path=src_path,
        opener=custom_netcdf_opener,
        opener_options={"special_arg": True},
        variable="dataset",
    ) as src:
        assert src.info()

    with pytest.raises(ValueError):
        with Reader(
            src_path=src_path,
            opener=custom_netcdf_opener,
            opener_options={"special_arg": False},
            variable="dataset",
        ) as src:
            pass


@pytest.mark.parametrize(
    "group",
    [0, 1, 2],
)
def test_zarr_group(group):
    """test reader."""
    src_path = os.path.join(prefix, "pyramid.zarr")

    with Reader(src_path, variable="dataset", group=str(group)) as src:
        assert src.info()
        assert src.tile(0, 0, 0)
        assert src.point(0, 0).data[0] == group * 2 + 1


@pytest.mark.parametrize(
    "src_path",
    [
        # "s3://mur-sst/zarr-v1",
        "https://nasa-power.s3.amazonaws.com/syn1deg/temporal/power_syn1deg_monthly_temporal_lst.zarr",
        os.path.join(prefix, "dataset_3d.zarr"),
    ],
)
def test_io_xarray_open_dataset(src_path):
    """test xarray_open_dataset with cloud hosted files."""
    with xarray_open_dataset(src_path) as ds:
        assert list(ds.data_vars)
