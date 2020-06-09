
# Cloud Optimized GeoTIFF - COG

## Tiles

`:endpoint:/cog/tiles/[{TileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{ext}]`

- PathParams:
    - **TileMatrixSetId**: TileMatrixSet name, default is `WebMercatorQuad`. OPTIONAL
    - **z**: Mercator tiles's zoom level.
    - **x**: Mercator tiles's column.
    - **y**: Mercator tiles's row.
    - **scale**: Tile size scale, default is set to 1 (256x256). OPTIONAL
    - **ext**: Output image format, default is set to None and will be either JPEG or PNG depending on masked value. OPTIONAL

- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**
    - **bidx**: Comma (',') delimited band indexes. OPTIONAL
    - **expression**: rio-tiler's band math expression (e.g B1/B2). OPTIONAL
    - **nodata**: Overwrite internal Nodata value. OPTIONAL
    - **rescale**: Comma (',') delimited Min,Max bounds. OPTIONAL
    - **color_formula**: rio-color formula. OPTIONAL
    - **color_map**: rio-tiler color map name. OPTIONAL

Example: 
- `https://myendpoint/cog/tiles/1/2/3?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/tiles/1/2/3.jpg?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/tiles/WorldCRS84Quad/1/2/3@2x.png?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/tiles/WorldCRS84Quad/1/2/3?url=https://somewhere.com/mycog.tif&bidx=1,2,3&rescale=0,1000&color_map=cfastie`

## TilesJSON

`:endpoint:/cog/[{TileMatrixSetId}]/tilejson.json` - Get tileJSON document

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

## Bounds

`:endpoint:/cog/bounds` - Get general image bounds

- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**

Example: 
- `https://myendpoint/cog/bounds?url=https://somewhere.com/mycog.tif`


## Info

`:endpoint:/cog/info` - Get general raster info
- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**

Example: 
- `https://myendpoint/cog/info?url=https://somewhere.com/mycog.tif`

## Metadata

`:endpoint:/cog/metadata` - Get raster statistics

- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**
    - **bidx**: Comma (',') delimited band indexes. OPTIONAL
    - **nodata**: Overwrite internal Nodata value. OPTIONAL
    - **pmin**: min percentile, default is 2. OPTIONAL
    - **pmax**: max percentile, default is 98. OPTIONAL
    - **max_size**: Max image size from which to calculate statistics, default is 1024. OPTIONAL
    - **histogram_bins**: Histogram bins, default is 20. OPTIONAL
    - **histogram_range**: Comma (',') delimited histogram bounds. OPTIONAL

Example: 
- `https://myendpoint/cog/metadata?url=https://somewhere.com/mycog.tif&bidx=1,2,3`


## Demo

`:endpoint:/cog/viewer` - COG Viewer

- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **OPTIONAL**

Example: 
- `https://myendpoint/cog/viewer?url=https://somewhere.com/mycog.tif`
