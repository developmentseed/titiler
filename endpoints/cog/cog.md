# Cloud Optimized GeoTIFF

Read Info/Metadata and create Web map Tiles from a **single** COG.

```python
# Minimal FastAPI app with COG support
from titiler.endpoints import cog

from fastapi import FastAPI

app = FastAPI()

# The COG Tiler is created with the TilerFactory with the `cog` prefix
app.include_router(cog.router, prefix="/cog", tags=["Cloud Optimized GeoTIFF"])
```

## API

| Method | URL                                                                 | Output    | Description
| ------ | ------------------------------------------------------------------- |---------- |--------------
| `GET`  | `/cog/bounds`                                                       | JSON      | return bounds info for a dataset
| `GET`  | `/cog/info`                                                         | JSON      | return basic info for a dataset
| `GET`  | `/cog/info.geojson`                                                 | GeoJSON   | return basic info for a dataset as a GeoJSON feature
| `GET`  | `/cog/metadata`                                                     | JSON      | return info and statistics for a dataset
| `GET`  | `/cog/tiles/[{TileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`  | image/bin | create a web map tile image from a dataset
| `GET`  | `/cog/[{TileMatrixSetId}]/tilejson.json`                            | JSON      | return a Mapbox TileJSON document
| `GET`  | `/cog/{TileMatrixSetId}/WMTSCapabilities.xml`                       | XML       | return OGC WMTS Get Capabilities
| `GET`  | `/cog/point/{lon},{lat}`                                            | JSON      | return pixel value from a dataset
| `GET`  | `/cog/preview[.{format}]`                                           | image/bin | create a preview image from a dataset
| `GET`  | `/cog/crop/{minx},{miny},{maxx},{maxy}[/{width}x{height}].{format}` | image/bin | create an image from part of a dataset
| `GET`  | `/cog/validate`                                                     | JSON      | validate a COG and return dataset info
| `GET`  | `/cog/viewer`                                                       | HTML      | demo webpage

## Description

### Tiles

`:endpoint:/cog/tiles/[{TileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`

- PathParams:
    - **TileMatrixSetId**: TileMatrixSet name, default is `WebMercatorQuad`. OPTIONAL
    - **z**: Mercator tile's zoom level.
    - **x**: Mercator tile's column.
    - **y**: Mercator tile's row.
    - **scale**: Tile size scale, default is set to 1 (256x256). OPTIONAL
    - **format**: Output image format, default is set to None and will be either JPEG or PNG depending on masked value. OPTIONAL

- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**
    - **bidx**: Comma (',') delimited band indexes. OPTIONAL
    - **expression**: rio-tiler's band math expression (e.g B1/B2). OPTIONAL
    - **nodata**: Overwrite internal Nodata value. OPTIONAL
    - **rescale**: Comma (',') delimited Min,Max bounds. OPTIONAL
    - **color_formula**: rio-color formula. OPTIONAL
    - **color_map**: rio-tiler color map name. OPTIONAL
    - **resampling_method**: rasterio resampling method. Default is `nearest`.

Example:

- `https://myendpoint/cog/tiles/1/2/3?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/tiles/1/2/3.jpg?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/tiles/WorldCRS84Quad/1/2/3@2x.png?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/tiles/WorldCRS84Quad/1/2/3?url=https://somewhere.com/mycog.tif&bidx=1&rescale=0,1000&color_map=cfastie`

### Preview

`:endpoint:/cog/preview[.{format}]`

- PathParams:
    - **format**: Output image format, default is set to None and will be either JPEG or PNG depending on masked value. OPTIONAL

- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**
    - **bidx**: Comma (',') delimited band indexes. OPTIONAL
    - **expression**: rio-tiler's band math expression (e.g B1/B2). OPTIONAL
    - **nodata**: Overwrite internal Nodata value. OPTIONAL
    - **max_size**: Max image size, default is 1024. OPTIONAL
    - **height**: Force output image height. OPTIONAL
    - **width**: Force output image width. OPTIONAL
    - **rescale**: Comma (',') delimited Min,Max bounds. OPTIONAL
    - **color_formula**: rio-color formula. OPTIONAL
    - **color_map**: rio-tiler color map name. OPTIONAL
    - **resampling_method**: rasterio resampling method. Default is `nearest`.

Note: if `height` and `width` are provided `max_size` will be ignored.

Example:

- `https://myendpoint/cog/preview?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/preview.jpg?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/preview?url=https://somewhere.com/mycog.tif&bidx=1&rescale=0,1000&color_map=cfastie`

### Crop / Part

`:endpoint:/cog/crop/{minx},{miny},{maxx},{maxy}.{format}`
`:endpoint:/cog/crop/{minx},{miny},{maxx},{maxy}/{width}x{height}.{format}`

- PathParams:
    - **minx,miny,maxx,maxy**: Comma (',') delimited bounding box in WGS84.
    - **format**: Output image format
    - **height**: Force output image height. OPTIONAL
    - **width**: Force output image width. OPTIONAL

- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**
    - **bidx**: Comma (',') delimited band indexes. OPTIONAL
    - **expression**: rio-tiler's band math expression (e.g B1/B2). OPTIONAL
    - **nodata**: Overwrite internal Nodata value. OPTIONAL
    - **max_size**: Max image size, default is 1024. OPTIONAL
    - **rescale**: Comma (',') delimited Min,Max bounds. OPTIONAL
    - **color_formula**: rio-color formula. OPTIONAL
    - **color_map**: rio-tiler color map name. OPTIONAL
    - **resampling_method**: rasterio resampling method. Default is `nearest`.

Note: if `height` and `width` are provided `max_size` will be ignored.

Example:

- `https://myendpoint/cog/crop/0,0,10,10.png?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/crop/0,0,10,10.png?url=https://somewhere.com/mycog.tif&bidx=1&rescale=0,1000&color_map=cfastie`

### Point

`:endpoint:/cog/point/{lon},{lat}`

- PathParams:
    - **lon,lat,**: Comma (',') delimited point Longitude and Latitude WGS84.

- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**
    - **bidx**: Comma (',') delimited band indexes. OPTIONAL
    - **expression**: rio-tiler's band math expression (e.g B1/B2). OPTIONAL
    - **nodata**: Overwrite internal Nodata value. OPTIONAL

Example:

- `https://myendpoint/cog/point/0,0?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/point/0,0?url=https://somewhere.com/mycog.tif&bidx=1`

### TilesJSON

`:endpoint:/cog/[{TileMatrixSetId}]/tilejson.json` tileJSON document

- PathParams:
    - **TileMatrixSetId**: TileMatrixSet name, default is `WebMercatorQuad`. OPTIONAL

- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**
    - **tile_format**: Output image format, default is set to None and will be either JPEG or PNG depending on masked value.
    - **tile_scale**: Tile size scale, default is set to 1 (256x256). OPTIONAL
    - **minzoom**: Overwrite default minzoom. OPTIONAL
    - **maxzoom**: Overwrite default maxzoom. OPTIONAL
    - **kwargs**: Other options will be forwarded to the `tiles` url.

Example:

- `https://myendpoint/cog/tilejson.json?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/tilejson.json?url=https://somewhere.com/mycog.tif&tile_format=png`
- `https://myendpoint/cog/WorldCRS84Quad/tilejson.json?url=https://somewhere.com/mycog.tif&tile_scale=2&bidx=1,2,3`

### Bounds

`:endpoint:/cog/bounds` general image bounds

- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**

Example:

- `https://myendpoint/cog/bounds?url=https://somewhere.com/mycog.tif`

### Info

`:endpoint:/cog/info` general raster info
- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**

Example:

- `https://myendpoint/cog/info?url=https://somewhere.com/mycog.tif`

`:endpoint:/cog/info.geojson` general raster info as a GeoJSON feature
- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**

Example:

- `https://myendpoint/cog/info.geojson?url=https://somewhere.com/mycog.tif`


### Metadata

`:endpoint:/cog/metadata` raster statistics

- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**
    - **bidx**: Comma (',') delimited band indexes. OPTIONAL
    - **nodata**: Overwrite internal Nodata value. OPTIONAL
    - **pmin**: min percentile, default is 2. OPTIONAL
    - **pmax**: max percentile, default is 98. OPTIONAL
    - **max_size**: Max image size from which to calculate statistics, default is 1024. OPTIONAL
    - **histogram_bins**: Histogram bins, default is 20. OPTIONAL
    - **histogram_range**: Comma (',') delimited histogram bounds. OPTIONAL
    - **resampling_method**: rasterio resampling method. Default is `nearest`.

Example:

- `https://myendpoint/cog/metadata?url=https://somewhere.com/mycog.tif&bidx=1,2,3`

### Demo

`:endpoint:/cog/viewer` - COG Viewer

- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **OPTIONAL**

Example:

- `https://myendpoint/cog/viewer?url=https://somewhere.com/mycog.tif`


### Validate

`:endpoint:/cog/validate` - COG Viewer

- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**
    - **strict**: Treat warnings as errors (bool, default is False). **OPTIONAL**

Example:

- `https://myendpoint/cog/validate?url=https://somewhere.com/mycog.tif`
