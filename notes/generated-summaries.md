
# Repo Summary

TiTiler is a Python-based geospatial tile server framework built on FastAPI and raster/GDAL tooling that turns geospatial datasets into dynamic web map tiles and APIs. It supports Cloud Optimized GeoTIFFs, STAC catalogs, MosaicJSON, OGC tile standards, multi-projection tiling, and xarray/Zarr datasets, and it is organized as a modular monorepo with separate packages for core tiling, extensions, applications, mosaic support, and xarray integration so teams can deploy scalable, standards-based map services in local, Docker, AWS, and Kubernetes environments.

Notes:
* Tile server: divides geographic data into small images
  * Tiles are vector pieces
  * The server will deliver htem on demand
  * How mapping appliactions use them:
    * Request only the tiles needed for the current location and zoom level
    * X, Y, Z (zoom)
    * When you're zoomed in at level 8, request however many tiles you need to show on the screen

# Request Route

* main.py sets up the frameowkr
  * middleware
* TilerFactory
  * dataclass
  * generates endpoints
* dependency injection managed through FastAPI
* small endpoint body (in the factory still)
* the actual read of the tiles (happnens outside this repo)
* post processing and rendering
  * still in the factory