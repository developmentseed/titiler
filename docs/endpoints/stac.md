# SpatioTemporal Asset Catalog

Read Info/Metadata and create Web map Tiles from a **single** STAC Item.

```python
# Minimal FastAPI app with COG support
from titiler.endpoints import stac

from fastapi import FastAPI

app = FastAPI()

# The STAC Tiler is created with the TilerFactory with the `stac` prefix
app.include_router(stac.router, prefix="/stac", tags=["SpatioTemporal Asset Catalog"])
```

## API

| Method | URL                                                                 | Output    | Description
| ------ | ------------------------------------------------------------------- |---------- |--------------
| `GET`  | `/stac/bounds`                                                       | JSON      | return bounds info for a dataset
| `GET`  | `/stac/info`                                                         | JSON      | return basic info for a dataset
| `GET`  | `/stac/info.geojson`                                                 | GeoJSON   | return basic info for a dataset as a GeoJSON feature
| `GET`  | `/stac/metadata`                                                     | JSON      | return info and statistics for a dataset
| `GET`  | `/stac/tiles/[{TileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`  | image/bin | create a web map tile image from a dataset
| `GET`  | `/stac/[{TileMatrixSetId}]/tilejson.json`                            | JSON      | return a Mapbox TileJSON document
| `GET`  | `/stac/{TileMatrixSetId}/WMTSCapabilities.xml`                       | XML       | return OGC WMTS Get Capabilities
| `GET`  | `/stac/point/{lon},{lat}`                                            | JSON      | return pixel value from a dataset
| `GET`  | `/stac/preview[.{format}]`                                           | image/bin | create a preview image from a dataset
| `GET`  | `/stac/crop/{minx},{miny},{maxx},{maxy}[/{width}x{height}].{format}` | image/bin | create an image from part of a dataset
| `GET`  | `/stac/viewer`                                                       | HTML      | demo webpage

## Description

### Tiles

`:endpoint:/stac/tiles/[{TileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`

- PathParams:
    - **TileMatrixSetId**: TileMatrixSet name, default is `WebMercatorQuad`. OPTIONAL
    - **z**: Mercator tiles's zoom level.
    - **x**: Mercator tiles's column.
    - **y**: Mercator tiles's row.
    - **scale**: Tile size scale, default is set to 1 (256x256). OPTIONAL
    - **format**: Output image format, default is set to None and will be either JPEG or PNG depending on masked value. OPTIONAL

- QueryParams:
    - **url**: STAC Item URL. **REQUIRED**
    - **assets**: Comma (',') delimited asset names. OPTIONAL*
    - **expression**: rio-tiler's band math expression (e.g B1/B2). OPTIONAL*
    - **bidx**: Comma (',') delimited band indexes. OPTIONAL
    - **nodata**: Overwrite internal Nodata value. OPTIONAL
    - **rescale**: Comma (',') delimited Min,Max bounds. OPTIONAL
    - **color_formula**: rio-color formula. OPTIONAL
    - **color_map**: rio-tiler color map name. OPTIONAL
    - **resampling_method**: rasterio resampling method. Default is `nearest`.

***assets** OR **expression** is required

Example:

- `https://myendpoint/stac/tiles/1/2/3?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/tiles/1/2/3.jpg?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/tiles/WorldCRS84Quad/1/2/3@2x.png?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/tiles/WorldCRS84Quad/1/2/3?url=https://somewhere.com/item.json&expression=B01/B02&rescale=0,1000&color_map=cfastie`


### Preview

`:endpoint:/stac/preview[.{format}]`

- PathParams:
    - **format**: Output image format, default is set to None and will be either JPEG or PNG depending on masked value. OPTIONAL

- QueryParams:
    - **url**: STAC Item URL. **REQUIRED**
    - **assets**: Comma (',') delimited asset names. OPTIONAL*
    - **expression**: rio-tiler's band math expression (e.g B1/B2). OPTIONAL
    - **bidx**: Comma (',') delimited band indexes. OPTIONAL
    - **nodata**: Overwrite internal Nodata value. OPTIONAL
    - **max_size**: Max image size, default is 1024. OPTIONAL
    - **height**: Force output image height. OPTIONAL
    - **width**: Force output image width. OPTIONAL
    - **rescale**: Comma (',') delimited Min,Max bounds. OPTIONAL
    - **color_formula**: rio-color formula. OPTIONAL
    - **color_map**: rio-tiler color map name. OPTIONAL

***assets** OR **expression** is required

Note: if `height` and `width` are provided `max_size` will be ignored.

Example:

- `https://myendpoint/stac/preview?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/preview.jpg?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/preview?url=https://somewhere.com/item.json&assets=B01&rescale=0,1000&color_map=cfastie`

### Crop / Part

`:endpoint:/stac/crop/{minx},{miny},{maxx},{maxy}.{format}`
`:endpoint:/stac/crop/{minx},{miny},{maxx},{maxy}/{width}x{height}.{format}`

- PathParams:
    - **minx,miny,maxx,maxy**: Comma (',') delimited bounding box in WGS84.
    - **format**: Output image format
    - **height**: Force output image height. OPTIONAL
    - **width**: Force output image width. OPTIONAL

- QueryParams:
    - **url**: STAC Item URL. **REQUIRED**
    - **assets**: Comma (',') delimited asset names. OPTIONAL*
    - **expression**: rio-tiler's band math expression (e.g B1/B2). OPTIONAL
    - **bidx**: Comma (',') delimited band indexes. OPTIONAL
    - **nodata**: Overwrite internal Nodata value. OPTIONAL

    - **rescale**: Comma (',') delimited Min,Max bounds. OPTIONAL
    - **color_formula**: rio-color formula. OPTIONAL
    - **color_map**: rio-tiler color map name. OPTIONAL
    - **resampling_method**: rasterio resampling method. Default is `nearest`.

***assets** OR **expression** is required

Note: if `height` and `width` are provided `max_size` will be ignored.

Example:

- `https://myendpoint/stac/crop/0,0,10,10.png?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/crop/0,0,10,10.png?url=https://somewhere.com/item.json&assets=B01&rescale=0,1000&color_map=cfastie`

### Point

`:endpoint:/cog/point/{lon},{lat}`

- PathParams:
    - **lon,lat,**: Comma (',') delimited point Longitude and Latitude WGS84.

- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**
    - **assets**: Comma (',') delimited asset names. OPTIONAL*
    - **expression**: rio-tiler's band math expression (e.g B1/B2). OPTIONAL
    - **bidx**: Comma (',') delimited band indexes. OPTIONAL
    - **nodata**: Overwrite internal Nodata value. OPTIONAL

***assets** OR **expression** is required

Example:

- `https://myendpoint/stac/point/0,0?url=https://somewhere.com/item.json&assets=B01`

### TilesJSON

`:endpoint:/stac/[{TileMatrixSetId}]/tilejson.json` tileJSON document

- PathParams:
    - **TileMatrixSetId**: TileMatrixSet name, default is `WebMercatorQuad`. OPTIONAL

- QueryParams:
    - **url**: STAC Item URL. **REQUIRED**
    - **assets**: Comma (',') delimited asset names. OPTIONAL*
    - **expression**: rio-tiler's band math expression (e.g B1/B2). OPTIONAL*
    - **tile_format**: Output image format, default is set to None and will be either JPEG or PNG depending on masked value.
    - **tile_scale**: Tile size scale, default is set to 1 (256x256). OPTIONAL
    - **minzoom**: Overwrite default minzoom, default is set to 0 by stac-tiler. OPTIONAL
    - **maxzoom**: Overwrite default maxzoom, default is set to 24 by stac-tiler. OPTIONAL
    - **kwargs**: Other options will be forwarded to the `tiles` url.

***assets** OR **expression** is required

Example:

- `https://myendpoint/stac/tilejson.json?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/tilejson.json?url=https://somewhere.com/item.json&assets=B01&tile_format=png`
- `https://myendpoint/stac/WorldCRS84Quad/tilejson.json?url=https://somewhere.com/item.json&tile_scale=2&expression=B01/B02`

### Bounds

`:endpoint:/stac/bounds` - Return the bounds of the STAC item.

- QueryParams:
    - **url**: STAC Item URL. **REQUIRED**

Example:

- `https://myendpoint/stac/bounds?url=https://somewhere.com/item.json`


### Info

`:endpoint:/stac/info` - Return basic info on STAC item's COG.

- QueryParams:
    - **url**: STAC Item URL. **REQUIRED**
    - **assets**: Comma (',') delimited asset names. OPTIONAL

Note: If `assets` is not provided, `/stac/info` will return the list of assets.

Example:

- `https://myendpoint/stac/info?url=https://somewhere.com/item.json&assets=B01`

`:endpoint:/stac/info.geojson` - Return basic info on STAC item's COG as a GeoJSON feature

- QueryParams:
    - **url**: STAC Item URL. **REQUIRED**
    - **assets**: Comma (',') delimited asset names. OPTIONAL

Note: If `assets` is not provided, `/stac/info.geojson` will return the list of assets in the properties.

Example:

- `https://myendpoint/stac/info.geojson?url=https://somewhere.com/item.json&assets=B01`


### Metadata

`:endpoint:/stac/metadata` - Return metadata of STAC item's COG.

- QueryParams:
    - **url**: STAC Item URL. **REQUIRED**
    - **assets**: Comma (',') delimited asset names. **REQUIRED**
    - **bidx**: comma (',') delimited band indexes. OPTIONAL
    - **nodata**: Overwrite internal Nodata value. OPTIONAL
    - **pmin**: min percentile, default is 2. OPTIONAL
    - **pmax**: max percentile, default is 98. OPTIONAL
    - **max_size**: Max image size from which to calculate statistics, default is 1024. OPTIONAL
    - **histogram_bins**: Histogram bins, default is 20. OPTIONAL
    - **histogram_range**: comma (',') delimited histogram bounds. OPTIONAL
    - **resampling_method**: rasterio resampling method. Default is `nearest`.

Example:

- `https://myendpoint/stac/metadata?https://somewhere.com/item.json&assets=B01`

### Demo

`:endpoint:/stac/viewer` - STAC viewer

- QueryParams:
    - **url**: STAC Item URL. **OPTIONAL**

Example:

- `https://myendpoint/stac/viewer?url=https://somewhere.com/item.json`

