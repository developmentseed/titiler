
The `titiler.application` package comes with a full FastAPI application with COG, STAC and MosaicJSON supports.

# MosaicJSON

Read Mosaic Info/Metadata and create Web map Tiles from a multiple COG. The `mosaic` router is built on top of `titiler.mosaic.factor.MosaicTilerFactory`.

## API

| Method | URL                                                             | Output    | Description
| ------ | --------------------------------------------------------------- |---------- |--------------
| `GET`  | `/mosaicjson/`                                                             | JSON      | return a MosaicJSON document
| `GET`  | `/mosaicjson/bounds`                                                       | JSON      | return bounds info for a MosaicJSON
| `GET`  | `/mosaicjson/info`                                                         | JSON      | return basic info for a MosaicJSON
| `GET`  | `/mosaicjson/info.geojson`                                                 | GeoJSON   | return basic info for a MosaicJSON as a GeoJSON feature
| `GET`  | `/mosaicjson/tiles/[{TileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`  | image/bin | create a web map tile image from a MosaicJSON
| `GET`  | `/mosaicjson/[{TileMatrixSetId}]/tilejson.json`                            | JSON      | return a Mapbox TileJSON document
| `GET`  | `/mosaicjson/{TileMatrixSetId}/WMTSCapabilities.xml`                       | XML       | return OGC WMTS Get Capabilities
| `GET`  | `/mosaicjson/point/{lon},{lat}`                                            | JSON      | return pixel value from a MosaicJSON dataset

## Description

[TODO]
