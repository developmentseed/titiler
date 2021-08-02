
The `titiler.application` package comes with a full FastAPI application with COG, STAC and MosaicJSON supports.

# Cloud Optimized GeoTIFF

Read Info/Metadata and create Web map Tiles from a **single** COG. The `cog` router extend the default `titiler.core.factory.TilerFactory`.

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
| `POST` | `/cog/crop[/{width}x{height}][].{format}]`                          | image/bin | create an image from a geojson covering a dataset
| `GET`  | `/cog/statistics`                                                   | JSON      | Return advanced statistics from a dataset
| `POST` | `/cog/statistics`                                                   | GeoJSON   | Return zonal statistics from a dataset for a geosjon Feature or FeatureCollection
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
    - **colormap_name**: rio-tiler color map name. OPTIONAL
    - **colormap**: JSON encoded custom Colormap. OPTIONAL
    - **resampling_method**: rasterio resampling method. Default is `nearest`.

Example:

- `https://myendpoint/cog/tiles/1/2/3?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/tiles/1/2/3.jpg?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/tiles/WorldCRS84Quad/1/2/3@2x.png?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/tiles/WorldCRS84Quad/1/2/3?url=https://somewhere.com/mycog.tif&bidx=1&rescale=0,1000&colormap_name=cfastie`

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
    - **colormap_name**: rio-tiler color map name. OPTIONAL
    - **colormap**: JSON encoded custom Colormap. OPTIONAL
    - **resampling_method**: rasterio resampling method. Default is `nearest`.

Note: if `height` and `width` are provided `max_size` will be ignored.

Example:

- `https://myendpoint/cog/preview?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/preview.jpg?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/preview?url=https://somewhere.com/mycog.tif&bidx=1&rescale=0,1000&colormap_name=cfastie`

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
    - **colormap_name**: rio-tiler color map name. OPTIONAL
    - **colormap**: JSON encoded custom Colormap. OPTIONAL
    - **resampling_method**: rasterio resampling method. Default is `nearest`.

Example:

- `https://myendpoint/cog/crop/0,0,10,10.png?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/crop/0,0,10,10.png?url=https://somewhere.com/mycog.tif&bidx=1&rescale=0,1000&colormap_name=cfastie`


`:endpoint:/cog/crop[/{width}x{height}][].{format}] - [POST]`

- Body:
    - **feature**: A valid GeoJSON feature (Polygon or MultiPolygon)

- PathParams:
    - **height**: Force output image height. OPTIONAL
    - **width**: Force output image width. OPTIONAL
    - **format**: Output image format, default is set to None and will be either JPEG or PNG depending on masked value. OPTIONAL

- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**
    - **bidx**: Comma (',') delimited band indexes. OPTIONAL
    - **expression**: rio-tiler's band math expression (e.g B1/B2). OPTIONAL
    - **nodata**: Overwrite internal Nodata value. OPTIONAL
    - **max_size**: Max image size, default is 1024. OPTIONAL
    - **rescale**: Comma (',') delimited Min,Max bounds. OPTIONAL
    - **color_formula**: rio-color formula. OPTIONAL
    - **colormap_name**: rio-tiler color map name. OPTIONAL
    - **colormap**: JSON encoded custom Colormap. OPTIONAL
    - **resampling_method**: rasterio resampling method. Default is `nearest`.

Example:

- `https://myendpoint/cog/crop?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/crop.png?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/crop/100x100.png?url=https://somewhere.com/mycog.tif&bidx=1&rescale=0,1000&colormap_name=cfastie`

Note: if `height` and `width` are provided `max_size` will be ignored.

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

### Statistics

Advanced raster statistics

`:endpoint:/cog/statistics - [GET|POST]`

- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**
    - **bidx**: Comma (',') delimited band indexes. OPTIONAL
    - **expression**: rio-tiler's band math expression (e.g B1/B2). OPTIONAL
    - **nodata**: Overwrite internal Nodata value. OPTIONAL
    - **max_size**: Max image size from which to calculate statistics, default is 1024. OPTIONAL
    - **height**: Force image height. OPTIONAL
    - **width**: Force image width. OPTIONAL
    - **unscale**: Apply internal Scale/Offset. OPTIONAL
    - **resampling_method**: rasterio resampling method. Default is `nearest`.
    - **categorical**: Return statistics for categorical dataset.
    - **c** (multiple): Pixels values for categories.
    - **p** (multiple): Percentile values.

- Body (for POST endpoint):
    - **features**: A valid GeoJSON feature or FeatureCollection (Polygon or MultiPolygon).

Example:

- `https://myendpoint/cog/statistics?url=https://somewhere.com/mycog.tif&bidx=1,2,3&categorical=true&c=1&c=2&c=3&p=2&p98`

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
