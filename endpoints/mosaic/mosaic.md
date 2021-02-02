# MosaicJSON

Read Mosaic Info/Metadata and create Web map Tiles from a multiple COG.

```python
# Minimal FastAPI app with COG support
from titiler.endpoints import mosaic

from fastapi import FastAPI

app = FastAPI()

# The MosaicJSON Tiler is created with the MosaicTilerFactory with the `mosaicjson` prefix
app.include_router(mosaic.router, prefix="/mosaicjson", tags=["MosaicJSON"])
```

## API

| Method | URL                                                             | Output    | Description
| ------ | --------------------------------------------------------------- |---------- |--------------
| `GET`  | `/mosaicjson/`                                                             | JSON      | return a MosaicJSON document
| `POST` | `/mosaicjson/`                                                             | JSON      | create a MosaicJSON from a list of files
| `PUT`  | `/mosaicjson/`                                                             | JSON      | update a MosaicJSON from a list of files
| `GET`  | `/mosaicjson/bounds`                                                       | JSON      | return bounds info for a MosaicJSON
| `GET`  | `/mosaicjson/info`                                                         | JSON      | return basic info for a MosaicJSON
| `GET`  | `/mosaicjson/info.geojson`                                                 | GeoJSON   | return basic info for a MosaicJSON as a GeoJSON feature
| `GET`  | `/mosaicjson/tiles/[{TileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`  | image/bin | create a web map tile image from a MosaicJSON
| `GET`  | `/mosaicjson/[{TileMatrixSetId}]/tilejson.json`                            | JSON      | return a Mapbox TileJSON document
| `GET`  | `/mosaicjson/{TileMatrixSetId}/WMTSCapabilities.xml`                       | XML       | return OGC WMTS Get Capabilities
| `GET`  | `/mosaicjson/point/{lon},{lat}`                                            | JSON      | return pixel value from a MosaicJSON dataset

## Description

[TODO]
