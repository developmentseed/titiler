In addition to the `/cog`, `/stac` and `/mosaicjson` endpoints, the `titiler.application` package FastAPI application commes with additional metadata endpoints.

# Algorithms

## API

| Method | URL                          | Output          | Description
| ------ | ---------------------------- |---------------- |--------------
| `GET`  | `/algorithms`                | JSON            | retrieve the list of available Algorithms
| `GET`  | `/algorithms/{algorithmId}`  | JSON            | retrieve the metadata of the specified algorithm.

## Description


### List Algorithm

`:endpoint:/algorithm` - Get the list of supported TileMatrixSet

```bash
$ curl https://myendpoint/algorithms | jq

{
  "hillshade": {
    "title": "Hillshade",
    "description": "Create hillshade from DEM dataset.",
    "inputs": {
      "nbands": 1
    },
    "outputs": {
      "nbands": 1,
      "dtype": "uint8",
      "min": null,
      "max": null
    },
    "parameters": {
      "azimuth": {
        "default": 90,
        "maximum": 360,
        "minimum": 0,
        "title": "Azimuth",
        "type": "integer"
      },
      "angle_altitude": {
        "default": 90.0,
        "maximum": 90.0,
        "minimum": -90.0,
        "title": "Angle Altitude",
        "type": "number"
      },
      "buffer": {
        "default": 3,
        "maximum": 99,
        "minimum": 0,
        "title": "Buffer",
        "type": "integer"
      }
    }
  },
  ...
}
```

### Get Algorithm info

`:endpoint:/algorithms/{algorithmId}` - Get the algorithm metadata

- PathParams:
    - **algorithmId**: algorithm name

```bash
$ curl http://127.0.0.1:8000/algorithms/contours | jq

{
  "title": "Contours",
  "description": "Create contours from DEM dataset.",
  "inputs": {
    "nbands": 1
  },
  "outputs": {
    "nbands": 3,
    "dtype": "uint8",
    "min": null,
    "max": null
  },
  "parameters": {
    "increment": {
      "default": 35,
      "maximum": 999,
      "minimum": 0,
      "title": "Increment",
      "type": "integer"
    },
    "thickness": {
      "default": 1,
      "maximum": 10,
      "minimum": 0,
      "title": "Thickness",
      "type": "integer"
    },
    "minz": {
      "default": -12000,
      "maximum": 99999,
      "minimum": -99999,
      "title": "Minz",
      "type": "integer"
    },
    "maxz": {
      "default": 8000,
      "maximum": 99999,
      "minimum": -99999,
      "title": "Maxz",
      "type": "integer"
    }
  }
}
```
