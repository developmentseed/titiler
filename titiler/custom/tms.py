"""Custom TileMatrixSet."""

import morecantile
from rasterio.crs import CRS

# CUSTOM TMS for EPSG:3413
EPSG3413 = morecantile.TileMatrixSet.custom(
    (-4194300, -4194300, 4194300, 4194300),
    CRS.from_epsg(3413),
    identifier="EPSG3413",
    matrix_scale=[2, 2],
)

# CUSTOM TMS for EPSG:6933
# info from https://epsg.io/6933
EPSG6933 = morecantile.TileMatrixSet.custom(
    (-17357881.81713629, -7324184.56362408, 17357881.81713629, 7324184.56362408),
    CRS.from_epsg(6933),
    identifier="EPSG6933",
    matrix_scale=[1, 1],
)
