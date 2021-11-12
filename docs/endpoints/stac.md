
The `titiler.application` package comes with a full FastAPI application with COG, STAC and MosaicJSON supports.

# SpatioTemporal Asset Catalog

The `stac` router extend the default `titiler.core.factory.MultiBaseTilerFactory`.

```python
from fastapi import FastAPI
from titiler.application.routers.stac import stac

app = FastAPI()
app.include_router(stac.router, prefix="/stac", tags=["SpatioTemporal Asset Catalog"])
```

## API

| Method | URL                                                                  | Output    | Description
| ------ | -------------------------------------------------------------------- |---------- |--------------
| `GET`  | `/stac/assets`                                                       | JSON      | return available assets within the STAC item
| `GET`  | `/stac/bounds`                                                       | JSON      | return STAC item bounds
| `GET`  | `/stac/info`                                                         | JSON      | return asset's basic info
| `GET`  | `/stac/info.geojson`                                                 | GeoJSON   | return asset's basic info as a GeoJSON feature
| `GET`  | `/stac/statistics`                                                   | JSON      | return asset's statistics
| `POST` | `/stac/statistics`                                                   | GeoJSON   | return asset's statistics for a GeoJSON
| `GET`  | `/stac/tiles/[{TileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`  | image/bin | create a web map tile image from assets
| `GET`  | `/stac/[{TileMatrixSetId}]/tilejson.json`                            | JSON      | return a Mapbox TileJSON document
| `GET`  | `/stac/{TileMatrixSetId}/WMTSCapabilities.xml`                       | XML       | return OGC WMTS Get Capabilities
| `GET`  | `/stac/point/{lon},{lat}`                                            | JSON      | return pixel value from assets
| `GET`  | `/stac/preview[.{format}]`                                           | image/bin | create a preview image from assets
| `GET`  | `/stac/crop/{minx},{miny},{maxx},{maxy}[/{width}x{height}].{format}` | image/bin | create an image from part of assets
| `POST` | `/stac/crop[/{width}x{height}][].{format}]`                          | image/bin | create an image from a geojson covering the assets
| `GET`  | `/stac/viewer`                                                       | HTML      | demo webpage (Not in `MultiBaseTilerFactory`)

## Description

### Tiles

`:endpoint:/stac/tiles/[{TileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`

- PathParams:
    - **TileMatrixSetId** (str): TileMatrixSet name, default is `WebMercatorQuad`. **Optional**
    - **z** (int): TMS tile's zoom level.
    - **x** (int): TMS tile's column.
    - **y** (int): TMS tile's row.
    - **scale** (int): Tile size scale, default is set to 1 (256x256). **Optional**
    - **format** (str): Output image format, default is set to None and will be either JPEG or PNG depending on masked value. **Optional**

- QueryParams:
    - **url** (str): STAC Item URL. **Required**
    - **assets** (array[str]): asset names.
    - **expression** (str): rio-tiler's math expression with asset names (e.g `Asset1/Asset2`).
    - **asset_bidx** (array[str]): Per asset band math expression (e.g `Asset1|1,2,3`).
    - **asset_expression** (array[str]): Per asset band math expression (e.g `Asset1|b1\*b2`).
    - **nodata** (str, int, float): Overwrite internal Nodata value.
    - **unscale** (bool): Apply dataset internal Scale/Offset.
    - **resampling** (str): rasterio resampling method. Default is `nearest`.
    - **rescale** (array[str]): Comma (',') delimited Min,Max range (e.g `rescale=0,1000`, `rescale=0,1000&rescale=0,3000&rescale=0,2000`).
    - **color_formula** (str): rio-color formula.
    - **colormap** (str): JSON encoded custom Colormap.
    - **colormap_name** (str): rio-tiler color map name.
    - **return_mask** (bool): Add mask to the output data. Default is True.

!!! important
    **assets** OR **expression** is required

Example:

- `https://myendpoint/stac/tiles/1/2/3?url=https://somewhere.com/item.json&assets=B01&assets=B00`
- `https://myendpoint/stac/tiles/1/2/3.jpg?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/tiles/WorldCRS84Quad/1/2/3@2x.png?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/tiles/WorldCRS84Quad/1/2/3?url=https://somewhere.com/item.json&expression=B01/B02&rescale=0,1000&colormap_name=cfastie`

### Preview

`:endpoint:/stac/preview[.{format}]`

- PathParams:
    - **format**: Output image format, default is set to None and will be either JPEG or PNG depending on masked value. **Optional**

- QueryParams:
    - **url** (str): STAC Item URL. **Required**
    - **assets** (array[str]): asset names.
    - **expression** (str): rio-tiler's math expression with asset names (e.g `Asset1/Asset2`).
    - **asset_bidx** (array[str]): Per asset band math expression (e.g `Asset1|1,2,3`).
    - **asset_expression** (array[str]): Per asset band math expression (e.g `Asset1|b1\*b2`).
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
    - **assets** OR **expression** is required

    - if **height** and **width** are provided **max_size** will be ignored.

Example:

- `https://myendpoint/stac/preview?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/preview.jpg?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/preview?url=https://somewhere.com/item.json&assets=B01&rescale=0,1000&colormap_name=cfastie`

### Crop / Part

`:endpoint:/stac/crop/{minx},{miny},{maxx},{maxy}.{format}`
`:endpoint:/stac/crop/{minx},{miny},{maxx},{maxy}/{width}x{height}.{format}`

- PathParams:
    - **minx,miny,maxx,maxy** (str): Comma (',') delimited bounding box in WGS84.
    - **height** (int): Force output image height. **Optional**
    - **width** (int): Force output image width. **Optional**
    - **format** (str): Output image format, default is set to None and will be either JPEG or PNG depending on masked value. **Optional**

- QueryParams:
    - **url** (str): STAC Item URL. **Required**
    - **assets** (array[str]): asset names.
    - **expression** (str): rio-tiler's math expression with asset names (e.g `Asset1/Asset2`).
    - **asset_bidx** (array[str]): Per asset band math expression (e.g `Asset1|1,2,3`).
    - **asset_expression** (array[str]): Per asset band math expression (e.g `Asset1|b1\*b2`).
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
    - **assets** OR **expression** is required

    - if **height** and **width** are provided **max_size** will be ignored.

Example:

- `https://myendpoint/stac/crop/0,0,10,10.png?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/crop/0,0,10,10.png?url=https://somewhere.com/item.json&assets=B01&rescale=0,1000&colormap_name=cfastie`

`:endpoint:/stac/crop[/{width}x{height}][].{format}] - [POST]`

- Body:
    - **feature** (JSON): A valid GeoJSON feature (Polygon or MultiPolygon)

- PathParams:
    - **height** (int): Force output image height. **Optional**
    - **width** (int): Force output image width. **Optional**
    - **format** (str): Output image format, default is set to None and will be either JPEG or PNG depending on masked value. **Optional**

- QueryParams:
    - **url** (str): STAC Item URL. **Required**
    - **assets** (array[str]): asset names.
    - **expression** (str): rio-tiler's math expression with asset names (e.g `Asset1/Asset2`).
    - **asset_bidx** (array[str]): Per asset band math expression (e.g `Asset1|1,2,3`).
    - **asset_expression** (array[str]): Per asset band math expression (e.g `Asset1|b1\*b2`).
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
    - **assets** OR **expression** is required

    - if **height** and **width** are provided **max_size** will be ignored.

Example:

- `https://myendpoint/stac/crop?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/crop.png?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/crop/100x100.png?url=https://somewhere.com/item.json&assets=B01&rescale=0,1000&colormap_name=cfastie`

### Point

`:endpoint:/cog/point/{lon},{lat}`

- PathParams:
    - **lon,lat,** (str): Comma (',') delimited point Longitude and Latitude WGS84.

- QueryParams:
    - **url** (str): STAC Item URL. **Required**
    - **assets** (array[str]): asset names.
    - **expression** (str): rio-tiler's math expression with asset names (e.g `Asset1/Asset2`).
    - **asset_bidx** (array[str]): Per asset band math expression (e.g `Asset1|1,2,3`).
    - **asset_expression** (array[str]): Per asset band math expression (e.g `Asset1|b1\*b2`).
    - **nodata** (str, int, float): Overwrite internal Nodata value.
    - **unscale** (bool): Apply dataset internal Scale/Offset.
    - **resampling** (str): rasterio resampling method. Default is `nearest`.

!!! important
    **assets** OR **expression** is required

Example:

- `https://myendpoint/stac/point/0,0?url=https://somewhere.com/item.json&assets=B01`

### TilesJSON

`:endpoint:/stac/[{TileMatrixSetId}]/tilejson.json` tileJSON document

- PathParams:
    - **TileMatrixSetId**: TileMatrixSet name, default is `WebMercatorQuad`.

- QueryParams:
    - **url** (str): STAC Item URL. **Required**
    - **assets** (array[str]): asset names.
    - **expression** (str): rio-tiler's math expression with asset names (e.g `Asset1/Asset2`).
    - **asset_bidx** (array[str]): Per asset band math expression (e.g `Asset1|1,2,3`).
    - **asset_expression** (array[str]): Per asset band math expression (e.g `Asset1|b1\*b2`).
    - **tile_format** (str): Output image format, default is set to None and will be either JPEG or PNG depending on masked value.
    - **tile_scale** (int): Tile size scale, default is set to 1 (256x256).
    - **minzoom** (int): Overwrite default minzoom.
    - **maxzoom** (int): Overwrite default maxzoom.
    - **nodata** (str, int, float): Overwrite internal Nodata value.
    - **unscale** (bool): Apply dataset internal Scale/Offset.
    - **resampling** (str): rasterio resampling method. Default is `nearest`.
    - **rescale** (array[str]): Comma (',') delimited Min,Max range (e.g `rescale=0,1000`, `rescale=0,1000&rescale=0,3000&rescale=0,2000`).
    - **color_formula** (str): rio-color formula.
    - **colormap** (str): JSON encoded custom Colormap.
    - **colormap_name** (str): rio-tiler color map name.
    - **return_mask** (bool): Add mask to the output data. Default is True.

!!! important
    **assets** OR **expression** is required

Example:

- `https://myendpoint/stac/tilejson.json?url=https://somewhere.com/item.json&assets=B01`
- `https://myendpoint/stac/tilejson.json?url=https://somewhere.com/item.json&assets=B01&tile_format=png`
- `https://myendpoint/stac/WorldCRS84Quad/tilejson.json?url=https://somewhere.com/item.json&tile_scale=2&expression=B01/B02`

### Bounds

`:endpoint:/stac/bounds` - Return the bounds of the STAC item.

- QueryParams:
    - **url** (str): STAC Item URL. **Required**

Example:

- `https://myendpoint/stac/bounds?url=https://somewhere.com/item.json`


### Info

`:endpoint:/stac/info` - Return basic info on STAC item's COG.

- QueryParams:
    - **url** (str): STAC Item URL. **Required**
    - **assets** (array[str]): asset names. Default to all available assets.

Example:

- `https://myendpoint/stac/info?url=https://somewhere.com/item.json&assets=B01`

`:endpoint:/stac/info.geojson` - Return basic info on STAC item's COG as a GeoJSON feature

- QueryParams:
    - **url** (str): STAC Item URL. **Required**
    - **assets** (array[str]): asset names. Default to all available assets.

Example:

- `https://myendpoint/stac/info.geojson?url=https://somewhere.com/item.json&assets=B01`


`:endpoint:/stac/assets` - Return the list of available assets

Example:

- `https://myendpoint/stac/assets?url=https://somewhere.com/item.json`

### Statistics

`:endpoint:/stac/statistics - [GET]`

- QueryParams:
    - **url** (str): STAC Item URL. **Required**
    - **assets** (array[str]): asset names. Default to all available assets.
    - **asset_bidx** (array[str]): Per asset band math expression (e.g `Asset1|1,2,3`).
    - **asset_expression** (array[str]): Per asset band math expression (e.g `Asset1|b1\*b2`).
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

- `https://myendpoint/stac/statistics?url=https://somewhere.com/item.json&assets=B01&categorical=true&c=1&c=2&c=3&p=2&p98`


`:endpoint:/stac/statistics - [POST]`

- Body:
    - **feature** (JSON): A valid GeoJSON feature or FeatureCollection

- QueryParams:
    - **url** (str): STAC Item URL. **Required**
    - **assets** (array[str]): asset names. Default to all available assets.
    - **asset_bidx** (array[str]): Per asset band math expression (e.g `Asset1|1,2,3`).
    - **asset_expression** (array[str]): Per asset band math expression (e.g `Asset1|b1\*b2`).
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

- `https://myendpoint/stac/statistics?url=https://somewhere.com/item.json&assets=B01&categorical=true&c=1&c=2&c=3&p=2&p98`


### Demo

Demonstration viewer added to the router created by the factory (https://github.com/developmentseed/titiler/blob/1f6b00cd50d60acae7b41ee108f80ad08fa52094/titiler/endpoints/stac.py#L14-L26).

`:endpoint:/stac/viewer` - STAC viewer

- QueryParams:
    - **url**: STAC Item URL. **Optional**

Example:

- `https://myendpoint/stac/viewer?url=https://somewhere.com/item.json`
