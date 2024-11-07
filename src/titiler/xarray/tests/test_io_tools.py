"""test titiler.xarray.io utility functions."""

import os
from datetime import datetime

import numpy
import pytest
import xarray

from titiler.xarray.io import Reader, get_variable

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
    assert da.dims == ("y", "x")
    # Default to the first Time value
    assert da["time"] == numpy.datetime64("2022-01-01")

    da = get_variable(ds, "dataset", datetime="2023-01-01T01:00:00.000Z")
    assert da.rio.crs
    assert da.dims == ("y", "x")
    assert da["time"] == numpy.datetime64("2023-01-01")

    # Select the Nearest Time
    da = get_variable(ds, "dataset", datetime="2024-01-01T01:00:00.000Z")
    assert da.rio.crs
    assert da.dims == ("y", "x")
    assert da["time"] == numpy.datetime64("2023-01-01")

    data = data.rename({"y": "Lat", "x": "Lon"})
    assert data.dims == ("time", "Lat", "Lon")
    ds = data.to_dataset(name="dataset")
    da = get_variable(ds, "dataset")
    assert da.rio.crs
    assert da.dims == ("y", "x")

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
    da = get_variable(ds, "dataset")
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
    ds = data.to_dataset(name="dataset")
    with pytest.raises(AssertionError):
        get_variable(ds, "dataset")

    da = get_variable(ds, "dataset", drop_dim="universe=somewhere")
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


@pytest.mark.parametrize(
    "group",
    [0, 1, 2],
)
def test_zarr_group(group):
    """test reader."""
    src_path = os.path.join(prefix, "pyramid.zarr")

    with Reader(src_path, variable="dataset", group=group) as src:
        assert src.info()
        assert src.tile(0, 0, 0)
        assert src.point(0, 0).data[0] == group * 2 + 1
