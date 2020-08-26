# SpatioTemporal Asset Catalog

## Tiles - GET

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

Additional parameters can be provided. See:

- https://github.com/cogeotiff/rio-tiler/blob/master/rio_tiler/reader.py#L140-L151
- https://github.com/cogeotiff/rio-tiler/blob/master/rio_tiler/reader.py#L32-L44

Example:

- `https://myendpoint/stac/tiles/1/2/3?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/tiles/1/2/3.jpg?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/tiles/WorldCRS84Quad/1/2/3@2x.png?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/tiles/WorldCRS84Quad/1/2/3?url=https://somewhere.com/item.json&expression=B01/B02&rescale=0,1000&color_map=cfastie`


## Preview - GET

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

Additional parameters can be provided. See:

- https://github.com/cogeotiff/rio-tiler/blob/master/rio_tiler/reader.py#L32-L44

Note: if `height` and `width` are provided `max_size` will be ignored.

Example:

- `https://myendpoint/stac/preview?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/preview.jpg?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/preview?url=https://somewhere.com/item.json&assets=B01&rescale=0,1000&color_map=cfastie`

## Crop / Part - GET

`:endpoint:/stac/crop/{minx},{miny},{maxx},{maxy}.{format}`

- PathParams:
    - **minx,miny,maxx,maxy**: Comma (',') delimited bounding box in WGS84.
    - **format**: Output image format

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
    - **resampling_method**: rasterio resampling method. Default is `nearest`.

***assets** OR **expression** is required

Additional parameters can be provided. See:

- https://github.com/cogeotiff/rio-tiler/blob/master/rio_tiler/reader.py#L140-L151
- https://github.com/cogeotiff/rio-tiler/blob/master/rio_tiler/reader.py#L32-L44

Note: if `height` and `width` are provided `max_size` will be ignored.

Example:

- `https://myendpoint/stac/crop/0,0,10,10.png?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/crop/0,0,10,10.png?url=https://somewhere.com/item.json&assets=B01&rescale=0,1000&color_map=cfastie`

## Point - GET

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


## TilesJSON - GET

`:endpoint:/stac/[{TileMatrixSetId}]/tilejson.json` - Get tileJSON document

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

## Bounds - GET

`:endpoint:/stac/bounds` - Return the bounds of the STAC item.

- QueryParams:
    - **url**: STAC Item URL. **REQUIRED**

Example:

- `https://myendpoint/stac/bounds?url=https://somewhere.com/item.json`


## Info - GET

`:endpoint:/stac/info` - Return basic info on STAC item's COG.

- QueryParams:
    - **url**: STAC Item URL. **REQUIRED**
    - **assets**: Comma (',') delimited asset names. OPTIONAL

Note: If `assets` is not provided, `/stac/info` will return the list of assets.

Example:

- `https://myendpoint/stac/info?url=https://somewhere.com/item.json&assets=B01`

## Metadata - GET

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

## Demo - GET

`:endpoint:/stac/viewer` - STAC viewer

- QueryParams:
    - **url**: STAC Item URL. **OPTIONAL**

Example:

- `https://myendpoint/stac/viewer?url=https://somewhere.com/item.json`

