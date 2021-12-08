The `titiler.application` package comes with a full FastAPI application with COG, STAC and MosaicJSON supports.

# TileMatrixSets

The `tms` router extend the default `titiler.core.factory.TMSFactory`, adding some custom TileMatrixSets.

```python
from fastapi import FastAPI
from titiler.application.routers.tms import tms

app = FastAPI()
app.include_router(tms.router, tags=["TileMatrixSets"])
```


## API

| Method | URL                                 | Output    | Description
| ------ | ----------------------------------- |---------- |--------------
| `GET`  | `/tileMatrixSets`                   | JSON      | return the list of supported TileMatrixSet
| `GET`  | `/tileMatrixSets/{TileMatrixSetId}` | JSON      | return the TileMatrixSet JSON document

## Description


### List TMS

`:endpoint:/tileMatrixSets` - Get the list of supported TileMatrixSet

```bash
$ curl https://myendpoint/tileMatrixSets | jq

{
  "tileMatrixSets": [
    {
      "id": "LINZAntarticaMapTilegrid",
      "title": "LINZ Antarctic Map Tile Grid (Ross Sea Region)",
      "links": [
        {
          "href": "https://myendpoint/tileMatrixSets/LINZAntarticaMapTilegrid",
          "rel": "item",
          "type": "application/json"
        }
      ]
    },
    ...
  ]
}
```

### Get TMS info

`:endpoint:/tileMatrixSets/{TileMatrixSetId}` - Get the TileMatrixSet JSON document

- PathParams:
    - **TileMatrixSetId**: TileMatrixSet name

```bash
$ curl http://127.0.0.1:8000/tileMatrixSets/WebMercatorQuad | jq

{
  "type": "TileMatrixSetType",
  "title": "Google Maps Compatible for the World",
  "identifier": "WebMercatorQuad",
  "supportedCRS": "http://www.opengis.net/def/crs/EPSG/0/3857",
  "wellKnownScaleSet": "http://www.opengis.net/def/wkss/OGC/1.0/GoogleMapsCompatible",
  "boundingBox": {
    "type": "BoundingBoxType",
    "crs": "http://www.opengis.net/def/crs/EPSG/0/3857",
    "lowerCorner": [
      -20037508.3427892,
      -20037508.3427892
    ],
    "upperCorner": [
      20037508.3427892,
      20037508.3427892
    ]
  },
  "tileMatrix": [
    {
      "type": "TileMatrixType",
      "identifier": "0",
      "scaleDenominator": 559082264.028717,
      "topLeftCorner": [
        -20037508.3427892,
        20037508.3427892
      ],
      "tileWidth": 256,
      "tileHeight": 256,
      "matrixWidth": 1,
      "matrixHeight": 1
    },
    ...
```
