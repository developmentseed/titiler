"""Create NetCDF fixture."""

import numpy as np
from netCDF4 import Dataset

# File name
filename = "testfile.nc"

# Create a new NetCDF file
rootgrp = Dataset(f"tests/fixtures/{filename}", "w", format="NETCDF4")

# Create dimensions
time = rootgrp.createDimension("time", 5)
lat = rootgrp.createDimension("lat", 100)
lon = rootgrp.createDimension("lon", 200)

# Create variables
times = rootgrp.createVariable("time", "f8", ("time",))
lats = rootgrp.createVariable("lat", "f4", ("lat",))
lons = rootgrp.createVariable("lon", "f4", ("lon",))
data = rootgrp.createVariable(
    "data",
    "f4",
    (
        "time",
        "lat",
        "lon",
    ),
    zlib=True,
)

# Fill variables with data
times[:] = np.arange(5)
lats[:] = np.linspace(-90, 90, 100)
lons[:] = np.linspace(-180, 180, 200)
data[:, :, :] = np.random.randint(-128, 127, size=(5, 100, 200), dtype=np.int8)

# Add some global attributes
rootgrp.description = "Test netCDF file with compressed data"
rootgrp.history = "Created " + np.datetime64("today", "D").astype(str)

# Close the NetCDF file
rootgrp.close()

print(f"{filename} has been created!")
