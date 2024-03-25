
The `titiler.application` package comes with a full FastAPI application with COG, STAC and MosaicJSON supports.

# MosaicJSON

Read Mosaic Info/Metadata and create Web map Tiles from a multiple COG. The `mosaic` router is built on top of `titiler.mosaic.factor.MosaicTilerFactory`.

## API

| Method | URL                                                                        | Output    | Description
| ------ | -------------------------------------------------------------------------- |---------- |--------------
| `GET`  | `/mosaicjson/`                                                             | JSON      | return a MosaicJSON document
| `GET`  | `/mosaicjson/bounds`                                                       | JSON      | return mosaic's bounds
| `GET`  | `/mosaicjson/info`                                                         | JSON      | return mosaic's basic info
| `GET`  | `/mosaicjson/info.geojson`                                                 | GeoJSON   | return mosaic's basic info as a GeoJSON feature
| `GET`  | `/mosaicjson/tiles/{tileMatrixSetId}/{z}/{x}/{y}[@{scale}x][.{format}]`  | image/bin | create a web map tile image from mosaic assets
| `GET`  | `/mosaicjson/{tileMatrixSetId}/tilejson.json`                            | JSON      | return a Mapbox TileJSON document
| `GET`  | `/mosaicjson/{tileMatrixSetId}/WMTSCapabilities.xml`                       | XML       | return OGC WMTS Get Capabilities
| `GET`  | `/mosaicjson/point/{lon},{lat}`                                            | JSON      | return pixel value from a mosaic assets
| `GET`  | `/mosaicjson/{z}/{x}/{y}/assets`                                           | JSON      | return list of assets intersecting a XYZ tile
| `GET`  | `/mosaicjson/{lon},{lat}/assets`                                           | JSON      | return list of assets intersecting a point
| `GET`  | `/mosaicjson/{minx},{miny},{maxx},{maxy}/assets`                           | JSON      | return list of assets intersecting a bounding box
| `GET`  | `/mosaicjson/{tileMatrixSetId}/map`                                      | HTML      | simple map viewer

## Description

[TODO]
