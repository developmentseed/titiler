"""Custom TileMatrixSet."""

import morecantile
from rasterio.crs import CRS

# CUSTOM TMS for EPSG:3413
extent = (-4194300, -4194300, 4194300, 4194300)
crs = CRS.from_epsg(3413)
EPSG3413 = morecantile.TileMatrixSet.custom(
    extent, crs, identifier="EPSG3413", matrix_scale=[2, 2]
)
