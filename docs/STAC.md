
# SpatioTemporal Asset Catalog - STAC

## Tiles

`:endpoint:/stac/tiles/[{TileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{ext}]`

- PathParams:
    - **TileMatrixSetId**: TileMatrixSet name, default is `WebMercatorQuad`. OPTIONAL
    - **z**: Mercator tiles's zoom level.
    - **x**: Mercator tiles's column.
    - **y**: Mercator tiles's row.
    - **scale**: Tile size scale, default is set to 1 (256x256). OPTIONAL
    - **ext**: Output image format, default is set to None and will be either JPEG or PNG depending on masked value. OPTIONAL

- QueryParams:
    - **url**: STAC Item URL. **REQUIRED**
    - **assets**: Comma (',') delimited asset names. OPTIONAL*
    - **expression**: rio-tiler's band math expression (e.g B1/B2). OPTIONAL*
    - **bidx**: Comma (',') delimited band indexes. OPTIONAL
    - **nodata**: Overwrite internal Nodata value. OPTIONAL
    - **rescale**: Comma (',') delimited Min,Max bounds. OPTIONAL
    - **color_formula**: rio-color formula. OPTIONAL
    - **color_map**: rio-tiler color map name. OPTIONAL

***assets** OR **expression** is required

Example: 
- `https://myendpoint/cog/tiles/1/2/3?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/cog/tiles/1/2/3.jpg?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/cog/tiles/WorldCRS84Quad/1/2/3@2x.png?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/cog/tiles/WorldCRS84Quad/1/2/3?url=https://somewhere.com/item.json&expression=B01/B02&rescale=0,1000&color_map=cfastie`

## TilesJSON

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

## Bounds

`:endpoint:/stac/bounds` - Return the bounds of the STAC item.

- QueryParams:
    - **url**: STAC Item URL. **REQUIRED**

Example: 
- `https://myendpoint/stac/bounds?url=https://somewhere.com/item.json`


## Info

`:endpoint:/stac/info` - Return basic info on STAC item's COG.
- QueryParams:
    - **url**: STAC Item URL. **REQUIRED**
    - **assets**: Comma (',') delimited asset names. OPTIONAL

Note: If `assets` is not provided, `/stac/info` will return the list of assets.

Example: 
- `https://myendpoint/stac/info?url=https://somewhere.com/item.json&assets=B01`

## Metadata

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

Example: 
- `https://myendpoint/stac/metadata?https://somewhere.com/item.json&assets=B01`

## Demo

`:endpoint:/stac/viewer` - STAC viewer

- QueryParams:
    - **url**: STAC Item URL. **OPTIONAL**

Example: 
- `https://myendpoint/stac/viewer?url=https://somewhere.com/item.json`

