""" Generate a pyramid for tests. """
from datetime import datetime

import numpy as np
import xarray as xr


def generate_random_pixel_data(n):
    """
    Generate random pixel data for a given number of pixels.
    """
    time_data = [datetime.now()]
    y_data = np.linspace(-90, 90, n)
    x_data = np.linspace(-180, 180, n)
    value_data = np.random.rand(n**2)
    return time_data, y_data, x_data, value_data


def create_dataset(time, y, x, value):
    """
    Create an xarray dataset from the given data.
    """
    return xr.Dataset(
        {
            "value": (("time", "y", "x"), value.reshape((1, len(y), len(x)))),
        },
        coords={
            "time": time,
            "y": y,
            "x": x,
        },
    )


time1, y1, x1, value1 = generate_random_pixel_data(10)
ds1 = create_dataset(time1, y1, x1, value1)

time2, y2, x2, value2 = generate_random_pixel_data(50)
ds2 = create_dataset(time2, y2, x2, value2)

time3, y3, x3, value3 = generate_random_pixel_data(250)
ds3 = create_dataset(time3, y3, x3, value3)

store_path = "tests/fixtures/pyramid.zarr"
ds1.to_zarr(store=f"{store_path}/0", mode="w")
ds2.to_zarr(store=f"{store_path}/1", mode="w")
ds3.to_zarr(store=f"{store_path}/2", mode="w")
