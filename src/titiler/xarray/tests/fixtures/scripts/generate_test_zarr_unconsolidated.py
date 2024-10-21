"""Create unconsolidated Zarr fixture."""

import numpy as np
import xarray as xr

# Create some sample data
times = np.arange(10)
lats = np.linspace(-90, 90, 90)
lons = np.linspace(-180, 180, 180)

data_var1 = np.random.rand(len(times), len(lats), len(lons))
data_var2 = np.random.rand(len(times), len(lats), len(lons))

# Create an xarray Dataset
ds = xr.Dataset(
    {
        "var1": (["time", "lat", "lon"], data_var1),
        "var2": (["time", "lat", "lon"], data_var2),
    },
    coords={"time": times, "lat": lats, "lon": lons},
)

# Save the dataset to a Zarr store
ds.to_zarr("unconsolidated.zarr", consolidated=False)

print("Zarr store created!")
