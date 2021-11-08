
The `titiler.application` package comes with a full FastAPI application with COG, STAC and MosaicJSON supports.

# Cloud Optimized GeoTIFF

The `cog` router extend the default `titiler.core.factory.TilerFactory`.

```python
from fastapi import FastAPI
from titiler.application.routers.cog import cog

app = FastAPI()
app.include_router(cog.router, prefix="/cog", tags=["Cloud Optimized GeoTIFF"])
```

## API

| Method | URL                                                                 | Output    | Description
| ------ | ------------------------------------------------------------------- |---------- |--------------
| `GET`  | `/cog/bounds`                                                       | JSON      | return dataset's bounds
| `GET`  | `/cog/info`                                                         | JSON      | return dataset's basic info
| `GET`  | `/cog/info.geojson`                                                 | GeoJSON   | return dataset's basic info as a GeoJSON feature
| `GET`  | `/cog/statistics`                                                   | JSON      | return dataset's statistics
| `POST` | `/cog/statistics`                                                   | GeoJSON   | return dataset's statistics for a GeoJSON
| `GET`  | `/cog/tiles/[{TileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`  | image/bin | create a web map tile image from a dataset
| `GET`  | `/cog/[{TileMatrixSetId}]/tilejson.json`                            | JSON      | return a Mapbox TileJSON document
| `GET`  | `/cog/{TileMatrixSetId}/WMTSCapabilities.xml`                       | XML       | return OGC WMTS Get Capabilities
| `GET`  | `/cog/point/{lon},{lat}`                                            | JSON      | return pixel values from a dataset
| `GET`  | `/cog/preview[.{format}]`                                           | image/bin | create a preview image from a dataset
| `GET`  | `/cog/crop/{minx},{miny},{maxx},{maxy}[/{width}x{height}].{format}` | image/bin | create an image from part of a dataset
| `POST` | `/cog/crop[/{width}x{height}][].{format}]`                          | image/bin | create an image from a GeoJSON feature
| `GET`  | `/cog/validate`                                                     | JSON      | validate a COG and return dataset info (Not in `TilerFactory`)
| `GET`  | `/cog/viewer`                                                       | HTML      | demo webpage (Not in `TilerFactory`)

## Description

### Tiles

`:endpoint:/cog/tiles/[{TileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`

- PathParams:
    - **TileMatrixSetId** (str): TileMatrixSet name, default is `WebMercatorQuad`. **Optional**
    - **z** (int): TMS tile's zoom level.
    - **x** (int): TMS tile's column.
    - **y** (int): TMS tile's row.
    - **scale** (int): Tile size scale, default is set to 1 (256x256). **Optional**
    - **format** (str): Output image format, default is set to None and will be either JPEG or PNG depending on masked value. **Optional**

- QueryParams:
    - **url** (str): Cloud Optimized GeoTIFF URL. **Required**
    - **bidx** (array[int]): Dataset band indexes (e.g `bidx=1`, `bidx=1&bidx=2&bidx=3`).
    - **expression** (str): rio-tiler's band math expression (e.g B1/B2).
    - **nodata** (str, int, float): Overwrite internal Nodata value.
    - **unscale** (bool): Apply dataset internal Scale/Offset.
    - **resampling** (str): rasterio resampling method. Default is `nearest`.
    - **rescale** (array[str]): Comma (',') delimited Min,Max range (e.g `rescale=0,1000`, `rescale=0,1000&rescale=0,3000&rescale=0,2000`).
    - **color_formula** (str): rio-color formula.
    - **colormap** (str): JSON encoded custom Colormap.
    - **colormap_name** (str): rio-tiler color map name.
    - **return_mask** (bool): Add mask to the output data. Default is True.

Example:

- `https://myendpoint/cog/tiles/1/2/3?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/tiles/1/2/3.jpg?url=https://somewhere.com/mycog.tif&bidx=3&bidx=1&bidx2`
- `https://myendpoint/cog/tiles/WorldCRS84Quad/1/2/3@2x.png?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/tiles/WorldCRS84Quad/1/2/3?url=https://somewhere.com/mycog.tif&bidx=1&rescale=0,1000&colormap_name=cfastie`

### Preview

`:endpoint:/cog/preview[.{format}]`

- PathParams:
    - **format** (str): Output image format, default is set to None and will be either JPEG or PNG depending on masked value. **Optional**

- QueryParams:
    - **url** (str): Cloud Optimized GeoTIFF URL. **Required**
    - **bidx** (array[int]): Dataset band indexes (e.g `bidx=1`, `bidx=1&bidx=2&bidx=3`).
    - **expression** (str): rio-tiler's band math expression (e.g B1/B2).
    - **max_size** (int): Max image size, default is 1024.
    - **height** (int): Force output image height.
    - **width** (int): Force output image width.
    - **nodata** (str, int, float): Overwrite internal Nodata value.
    - **unscale** (bool): Apply dataset internal Scale/Offset.
    - **resampling** (str): rasterio resampling method. Default is `nearest`.
    - **rescale** (array[str]): Comma (',') delimited Min,Max range (e.g `rescale=0,1000`, `rescale=0,1000&rescale=0,3000&rescale=0,2000`).
    - **color_formula** (str): rio-color formula.
    - **colormap** (str): JSON encoded custom Colormap.
    - **colormap_name** (str): rio-tiler color map name.
    - **return_mask** (bool): Add mask to the output data. Default is True.

!!! important
    if **height** and **width** are provided **max_size** will be ignored.

Example:

- `https://myendpoint/cog/preview?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/preview.jpg?url=https://somewhere.com/mycog.tif&bidx=3&bidx=1&bidx2`
- `https://myendpoint/cog/preview?url=https://somewhere.com/mycog.tif&bidx=1&rescale=0,1000&colormap_name=cfastie`

### Crop / Part

`:endpoint:/cog/crop/{minx},{miny},{maxx},{maxy}.{format}`
`:endpoint:/cog/crop/{minx},{miny},{maxx},{maxy}/{width}x{height}.{format}`

- PathParams:
    - **minx,miny,maxx,maxy** (str): Comma (',') delimited bounding box in WGS84.
    - **format** (str): Output image format
    - **height** (int): Force output image height.
    - **width** (int): Force output image width.

- QueryParams:
    - **url** (str): Cloud Optimized GeoTIFF URL. **Required**
    - **bidx** (array[int]): Dataset band indexes (e.g `bidx=1`, `bidx=1&bidx=2&bidx=3`).
    - **expression** (str): rio-tiler's band math expression (e.g B1/B2).
    - **max_size** (int): Max image size, default is 1024.
    - **nodata** (str, int, float): Overwrite internal Nodata value.
    - **unscale** (bool): Apply dataset internal Scale/Offset.
    - **resampling** (str): rasterio resampling method. Default is `nearest`.
    - **rescale** (array[str]): Comma (',') delimited Min,Max range (e.g `rescale=0,1000`, `rescale=0,1000&rescale=0,3000&rescale=0,2000`).
    - **color_formula** (str): rio-color formula.
    - **colormap** (str): JSON encoded custom Colormap.
    - **colormap_name** (str): rio-tiler color map name.
    - **return_mask** (bool): Add mask to the output data. Default is True.

!!! important
    if **height** and **width** are provided **max_size** will be ignored.

Example:

- `https://myendpoint/cog/crop/0,0,10,10.png?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/crop/0,0,10,10.png?url=https://somewhere.com/mycog.tif&bidx=1&rescale=0,1000&colormap_name=cfastie`


`:endpoint:/cog/crop[/{width}x{height}][].{format}] - [POST]`

- Body:
    - **feature** (JSON): A valid GeoJSON feature (Polygon or MultiPolygon)

- PathParams:
    - **height** (int): Force output image height. **Optional**
    - **width** (int): Force output image width. **Optional**
    - **format** (str): Output image format, default is set to None and will be either JPEG or PNG depending on masked value. **Optional**

- QueryParams:
    - **url** (str): Cloud Optimized GeoTIFF URL. **Required**
    - **bidx** (array[int]): Dataset band indexes (e.g `bidx=1`, `bidx=1&bidx=2&bidx=3`).
    - **expression** (str): rio-tiler's band math expression (e.g B1/B2).
    - **max_size** (int): Max image size, default is 1024.
    - **nodata** (str, int, float): Overwrite internal Nodata value.
    - **unscale** (bool): Apply dataset internal Scale/Offset.
    - **resampling** (str): rasterio resampling method. Default is `nearest`.
    - **rescale** (array[str]): Comma (',') delimited Min,Max range (e.g `rescale=0,1000`, `rescale=0,1000&rescale=0,3000&rescale=0,2000`).
    - **color_formula** (str): rio-color formula.
    - **colormap** (str): JSON encoded custom Colormap.
    - **colormap_name** (str): rio-tiler color map name.
    - **return_mask** (bool): Add mask to the output data. Default is True.

!!! important
    if **height** and **width** are provided **max_size** will be ignored.

Example:

- `https://myendpoint/cog/crop?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/crop.png?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/crop/100x100.png?url=https://somewhere.com/mycog.tif&bidx=1&rescale=0,1000&colormap_name=cfastie`

Note: if `height` and `width` are provided `max_size` will be ignored.

### Point

`:endpoint:/cog/point/{lon},{lat}`

- PathParams:
    - **lon,lat,** (str): Comma (',') delimited point Longitude and Latitude WGS84.

- QueryParams:
    - **url** (str): Cloud Optimized GeoTIFF URL. **Required**
    - **bidx** (array[int]): Dataset band indexes (e.g `bidx=1`, `bidx=1&bidx=2&bidx=3`).
    - **expression** (str): rio-tiler's band math expression (e.g B1/B2).
    - **nodata** (str, int, float): Overwrite internal Nodata value.
    - **unscale** (bool): Apply dataset internal Scale/Offset.
    - **resampling** (str): rasterio resampling method. Default is `nearest`.

Example:

- `https://myendpoint/cog/point/0,0?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/point/0,0?url=https://somewhere.com/mycog.tif&bidx=1`

### TilesJSON

`:endpoint:/cog/[{TileMatrixSetId}]/tilejson.json` tileJSON document

- PathParams:
    - **TileMatrixSetId**: TileMatrixSet name, default is `WebMercatorQuad`. **Optional**

- QueryParams:
    - **url** (str): Cloud Optimized GeoTIFF URL. **Required**
    - **tile_format** (str): Output image format, default is set to None and will be either JPEG or PNG depending on masked value.
    - **tile_scale** (int): Tile size scale, default is set to 1 (256x256).
    - **minzoom** (int): Overwrite default minzoom.
    - **maxzoom** (int): Overwrite default maxzoom.
    - **bidx** (array[int]): Dataset band indexes (e.g `bidx=1`, `bidx=1&bidx=2&bidx=3`).
    - **expression** (str): rio-tiler's band math expression (e.g B1/B2).
    - **nodata** (str, int, float): Overwrite internal Nodata value.
    - **unscale** (bool): Apply dataset internal Scale/Offset.
    - **resampling** (str): rasterio resampling method. Default is `nearest`.
    - **rescale** (array[str]): Comma (',') delimited Min,Max range (e.g `rescale=0,1000`, `rescale=0,1000&rescale=0,3000&rescale=0,2000`).
    - **color_formula** (str): rio-color formula.
    - **colormap** (str): JSON encoded custom Colormap.
    - **colormap_name** (str): rio-tiler color map name.
    - **return_mask** (bool): Add mask to the output data. Default is True.

Example:

- `https://myendpoint/cog/tilejson.json?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/tilejson.json?url=https://somewhere.com/mycog.tif&tile_format=png`
- `https://myendpoint/cog/WorldCRS84Quad/tilejson.json?url=https://somewhere.com/mycog.tif&tile_scale=2&bidx=1,2,3`

### Bounds

`:endpoint:/cog/bounds` general image bounds

- QueryParams:
    - **url** (str): Cloud Optimized GeoTIFF URL. **Required**

Example:

- `https://myendpoint/cog/bounds?url=https://somewhere.com/mycog.tif`

### Info

`:endpoint:/cog/info` general raster info

`:endpoint:/cog/info.geojson` general raster info as a GeoJSON feature

- QueryParams:
    - **url** (str): Cloud Optimized GeoTIFF URL. **Required**

Example:

- `https://myendpoint/cog/info?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/info.geojson?url=https://somewhere.com/mycog.tif`


### Statistics

Advanced raster statistics

`:endpoint:/cog/statistics - [GET]`

- QueryParams:
    - **url** (str): Cloud Optimized GeoTIFF URL. **Required**
    - **bidx** (array[int]): Dataset band indexes (e.g `bidx=1`, `bidx=1&bidx=2&bidx=3`).
    - **expression** (str): rio-tiler's band math expression (e.g B1/B2).
    - **max_size** (int): Max image size from which to calculate statistics, default is 1024.
    - **height** (int): Force image height from which to calculate statistics.
    - **width** (int): Force image width from which to calculate statistics.
    - **nodata** (str, int, float): Overwrite internal Nodata value.
    - **unscale** (bool): Apply dataset internal Scale/Offset.
    - **resampling** (str): rasterio resampling method. Default is `nearest`.
    - **categorical** (bool): Return statistics for categorical dataset, default is false.
    - **c** (array[float]): Pixels values for categories.
    - **p** (array[int]): Percentile values.
    - **histogram_bins** (str): Histogram bins.
    - **histogram_range** (str): Comma (',') delimited Min,Max histogram bounds

Example:

- `https://myendpoint/cog/statistics?url=https://somewhere.com/mycog.tif&bidx=1,2,3&categorical=true&c=1&c=2&c=3&p=2&p98`

`:endpoint:/cog/statistics - [POST]`

- Body:
    - **feature** (JSON): A valid GeoJSON feature or FeatureCollection

- QueryParams:
    - **url** (str): Cloud Optimized GeoTIFF URL. **Required**
    - **bidx** (array[int]): Dataset band indexes (e.g `bidx=1`, `bidx=1&bidx=2&bidx=3`).
    - **expression** (str): rio-tiler's band math expression (e.g B1/B2).
    - **max_size** (int): Max image size from which to calculate statistics, default is 1024.
    - **height** (int): Force image height from which to calculate statistics.
    - **width** (int): Force image width from which to calculate statistics.
    - **nodata** (str, int, float): Overwrite internal Nodata value.
    - **unscale** (bool): Apply dataset internal Scale/Offset.
    - **resampling** (str): rasterio resampling method. Default is `nearest`.
    - **categorical** (bool): Return statistics for categorical dataset, default is false.
    - **c** (array[float]): Pixels values for categories.
    - **p** (array[int]): Percentile values.
    - **histogram_bins** (str): Histogram bins.
    - **histogram_range** (str): Comma (',') delimited Min,Max histogram bounds

Example:

- `https://myendpoint/cog/statistics?url=https://somewhere.com/mycog.tif&bidx=1,2,3&categorical=true&c=1&c=2&c=3&p=2&p98`


### Demo

`:endpoint:/cog/viewer` - COG Viewer

- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **Required**

Example:

- `https://myendpoint/cog/viewer?url=https://somewhere.com/mycog.tif`


### Validate

`:endpoint:/cog/validate` - COG Viewer

- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **Required**
    - **strict**: Treat warnings as errors (bool, default is False).

Example:

- `https://myendpoint/cog/validate?url=https://somewhere.com/mycog.tif`
