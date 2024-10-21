"""Create zarr fixture."""

import numpy as np
import xarray as xr

# Define dimensions and chunk sizes
time_dim = 10
lat_dim = 36
lon_dim = 72
chunk_size = (10, 10, 10)

# Create coordinates
time = np.arange(time_dim)
lat = np.linspace(-90, 90, lat_dim)
lon = np.linspace(-180, 180, lon_dim, endpoint=False)

# Initialize variables with random data
CDD0 = xr.DataArray(
    np.random.rand(time_dim, lat_dim, lon_dim).astype(np.uint8),
    dims=("time", "lat", "lon"),
    name="CDD0",
)
DISPH = xr.DataArray(
    np.random.rand(time_dim, lat_dim, lon_dim).astype(np.uint8),
    dims=("time", "lat", "lon"),
    name="DISPH",
)
FROST_DAYS = xr.DataArray(
    np.random.rand(time_dim, lat_dim, lon_dim).astype(np.uint8),
    dims=("time", "lat", "lon"),
    name="FROST_DAYS",
)
GWETPROF = xr.DataArray(
    np.random.rand(time_dim, lat_dim, lon_dim).astype(np.uint8),
    dims=("time", "lat", "lon"),
    name="GWETPROF",
)

# Create dataset
ds = xr.Dataset(
    {
        "CDD0": CDD0.chunk(chunk_size),
        "DISPH": DISPH.chunk(chunk_size),
        "FROST_DAYS": FROST_DAYS.chunk(chunk_size),
        "GWETPROF": GWETPROF.chunk(chunk_size),
    },
    coords={"time": time, "lat": lat, "lon": lon},
)

# Save dataset to a local Zarr store
ds.to_zarr("fixtures/test_zarr_store.zarr", mode="w")
