# titiler

A lightweight Cloud Optimized GeoTIFF dynamic tile server.

[![CircleCI](https://circleci.com/gh/developmentseed/titiler.svg?style=svg)](https://circleci.com/gh/developmentseed/titiler)
[![codecov](https://codecov.io/gh/developmentseed/titiler/branch/master/graph/badge.svg)](https://codecov.io/gh/developmentseed/titiler)

Titiler, pronounced **tee-tiler** (*ti* is the diminutiveversion of the french *petit* which means small), is lightweight service, which sole goal is to create map tiles dynamically from Cloud Optimized GeoTIFF [COG](cogeo.org).

This project is the descendant of https://github.com/developmentseed/cogeo-tiler

Built on top of the *modern and fast* [FastAPI](https://fastapi.tiangolo.com) framework, titiler is written using async/await asynchronous code to improve the performances and handle heavy loads.

### Test locally
```bash
$ git clone https://github.com/developmentseed/titiler.git

$ cd titiler && pip install -e .["server"]
$ uvicorn titiler.main:app --reload
```
Or with Docker
```
$ docker-compose build
$ docker-compose up 
```

# API

## Doc

`:endpoint:/docs`

<details>

![](https://user-images.githubusercontent.com/10407788/83449203-33e8eb00-a421-11ea-8c78-6b12d368fad5.png)

</details>

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
    - **bidx**: Coma (',') delimited band indexes. OPTIONAL
    - **nodata**: Overwrite internal Nodata value. OPTIONAL
    - **rescale**: Coma (',') delimited Min,Max bounds. OPTIONAL
    - **color_formula**: rio-color formula. OPTIONAL
    - **color_map**: rio-tiler color map name. OPTIONAL

Example: 
- `https://myendpoint/cog/tiles/1/2/3?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/tiles/1/2/3.jpg?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/tiles/WorldCRS84Quad/1/2/3@2x.png?url=https://somewhere.com/mycog.tif`
- `https://myendpoint/cog/tiles/WorldCRS84Quad/1/2/3?url=https://somewhere.com/mycog.tif&bidx=1,2,3&rescale=0,1000&color_map=cfastie`

## TileMatrixSets


`:endpoint:/tileMatrixSets` - Get the list of supported TileMatrixSet

```
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

`:endpoint:/tileMatrixSets/{TileMatrixSetId}` - Get the TileMatrixSet JSON document

- PathParams:
    - **TileMatrixSetId**: TileMatrixSet name

```
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

## TilesJSON

`:endpoint:/cog/[{TileMatrixSetId}]/tilejson.json` - Get tileJSON document

- PathParams:
    - **TileMatrixSetId**: TileMatrixSet name, default is `WebMercatorQuad`. OPTIONAL

- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**
    - **tile_format**: Output image format, default is set to None and will be either JPEG or PNG depending on masked value.
    - **tile_scale**: Tile size scale, default is set to 1 (256x256). OPTIONAL
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

`:endpoint:/cog/info` - Get general image info
- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**

Example: 
- `https://myendpoint/cog/info?url=https://somewhere.com/mycog.tif`

## Metadata

`:endpoint:/cog/metadata` - Get image statistics

- QueryParams:
    - **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**
    - **bidx**: Coma (',') delimited band indexes. OPTIONAL
    - **nodata**: Overwrite internal Nodata value. OPTIONAL
    - **pmin**: min percentile, default is 2. OPTIONAL
    - **pmax**: max percentile, default is 98. OPTIONAL
    - **max_size**: Max image size from which to calculate statistics, default is 1024. OPTIONAL
    - **histogram_bins**: Histogram bins, default is 20. OPTIONAL
    - **histogram_range**: Coma (',') delimited histogram bounds. OPTIONAL

Example: 
- `https://myendpoint/cog/metadata?url=https://somewhere.com/mycog.tif&bidx=1,2,3`

## Demo

`:endpoint:/index.html` - Full UI (histogram, predefined rescaling, ...)

`:endpoint:/simple_viewer.html` - Simple UI (no histogram, manual rescaling, ...)

# Project structure

```
titiler/                         - titiler python module.
 ├── api/                        - general api directory.
 │   ├── api_                 - directory hosting version 1 of the API.
 │   │   ├── endpoints           - api routes.
 │   │   │   ├── metadata.py     - metadata endpoints (e.g. /tilesjson.json, /metadata...).
 │   │   │   ├── ogc.py          - OGC endpoints (e.g WMTS).
 │   │   │   ├── operations.py   - clip/points endpoints.
 │   │   │   ├── tiles.py        - tiling related endpoints.
 │   │   └── api.py              - construct the API by merging api_v1 endpoints.
 │   ├── deps.py                 - API dependencies.
 │   └── utils.py                - API utility functions.
 │
 ├── core/                       - application configuration.
 ├── custom/                     - Custom colormap and TMS grids.
 ├── db/                         - db related stuff.
 ├── models/                     - pydantic models for this application.
 ├── ressources/                 - application ressources (enums, constants, ...).
 ├── templates/                  - html/xml models.
 ├── main.py                     - FastAPI application creation and configuration.
 ├── utils.py                    - utility functions.
 │
stack/
 ├── app.py                      - AWS Stack definition (vpc, cluster, ecs, alb ...)
 ├── config.py                   - Optional parameters for the stack definition [EDIT THIS]
 │
Dockerfiles/
 ├── ecs/
 │   └── Dockerfile              - Dockerfile to build the ECS service image.
 ├── lambda/
 │   └── Dockerfile              - Dockerfile to build the Lambda service image.
 │
lambda/
 │   └── handler.py              - Mangum adaptator fro AWS Lambda.
 │
docs/
 └── openapi.json                - OpenAPI document.

```


## Deployment

To be able to deploy on either ECS or Lambda you first need to install more dependencies:

```bash
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler && pip install -e .["deploy"]
```

### ø AWS ECS (Fargate) + ALB (Application Load Balancer)
The stack is deployed by the [aws cdk](https://aws.amazon.com/cdk/) utility. It will handle tasks such as generating a docker image set up an application load balancer and the ECS services.

<details>

1. Instal cdk and set up CDK in your AWS account - Only need once per account
```bash
$ npm install cdk -g

$ cdk bootstrap # Deploys the CDK toolkit stack into an AWS environment
```

2. Pre-Generate CFN template
```bash
$ cdk synth  # Synthesizes and prints the CloudFormation template for this stack
```

3. Edit [stack/config.py](stack/config.py)

```python
PROJECT_NAME = "titiler"
STAGE = os.environ.get("STAGE", "dev")

# // Service config
# Min/Max Number of ECS images
MIN_ECS_INSTANCES = 2
MAX_ECS_INSTANCES = 50

# CPU value      |   Memory value
# 256 (.25 vCPU) | 0.5 GB, 1 GB, 2 GB
# 512 (.5 vCPU)  | 1 GB, 2 GB, 3 GB, 4 GB
# 1024 (1 vCPU)  | 2 GB, 3 GB, 4 GB, 5 GB, 6 GB, 7 GB, 8 GB
# 2048 (2 vCPU)  | Between 4 GB and 16 GB in 1-GB increments
# 4096 (4 vCPU)  | Between 8 GB and 30 GB in 1-GB increments
TASK_CPU = 1024
TASK_MEMORY = 2048
```

4. Deploy  
```bash
$ cdk deploy titiler-ecs-dev # Deploys the stack(s) titiler-ecs-dev in stack/app.py
```

</details>


### ø AWS Lambda 

Titiler is built on top of [FastAPI](https://github.com/tiangolo/fastapi) which *is a modern, fast (high-performance), web framework for building APIs*. It doesn't work natively with AWS Lambda and API Gateway because it needs a way to handler `event` and `context` instead of raw HTML requests. This is possible by wrapping the FastAPI app with the awesome [mangum](https://github.com/erm/mangum) module.


```python
from mangum import Mangum
from titiler.main import app

handler = Mangum(app, enable_lifespan=False)
```

The Lambda stack is also deployed by the [aws cdk](https://aws.amazon.com/cdk/) utility. It will create the `package.zip` and handle the creation of the lambda function and the API Gateway HTTP endpoint.

<details>

1. Instal cdk and set up CDK in your AWS account - Only need once per account
```bash
$ npm install cdk -g

$ cdk bootstrap # Deploys the CDK toolkit stack into an AWS environment
```

2. Pre-Generate CFN template
```bash
$ cdk synth  # Synthesizes and prints the CloudFormation template for this stack
```

3. Edit [stack/config.py](stack/config.py)

```python
PROJECT_NAME = "titiler"
STAGE = os.environ.get("STAGE", "dev")
...
TIMEOUT: int = 10
MEMORY: int = 512
MAX_CONCURRENT: int = 500
```

4. Deploy  
```bash
$ cdk deploy titiler-lambda-dev # Deploys the stack(s) titiler-lambda-dev in stack/app.py
```

</details>

## Contribution & Development

Issues and pull requests are more than welcome.

**dev install**

```bash
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler
$ pip install -e .[dev]
```

**Python3.7 only**

This repo is set to use `pre-commit` to run *my-py*, *flake8*, *pydocstring* and *black* ("uncompromising Python code formatter") when commiting new code.

```bash
$ pre-commit install
```

## Authors
Created by [Development Seed](<http://developmentseed.org>)

