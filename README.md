# titiler

A lightweight Cloud Optimized GeoTIFF tile server.

[![CircleCI](https://circleci.com/gh/developmentseed/titiler.svg?style=svg)](https://circleci.com/gh/developmentseed/titiler)
[![codecov](https://codecov.io/gh/developmentseed/titiler/branch/master/graph/badge.svg)](https://codecov.io/gh/developmentseed/titiler)

# Deployment

The stack is deployed by the [aws cdk](https://aws.amazon.com/cdk/) utility. It will handle tasks such as generating a docker image and packaging handlers automatically.

1. Instal cdk and set up CDK in your AWS account - Only need once per account
```bash
$ npm install cdk -g

$ cdk bootstrap # Deploys the CDK toolkit stack into an AWS environment
```

2. Install dependencies

```bash
# Note: it's recommanded to use virtualenv
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler && pip install -e .[deploy]
```

3. Pre-Generate CFN template
```bash
$ cdk synth  # Synthesizes and prints the CloudFormation template for this stack
```

4. Edit [stack/config.py](stack/config.py)

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

5. Deploy  
```bash
$ cdk deploy  # Deploys the stack(s) named STACKS into your AWS account
```

# Test locally
```bash
$ git clone https://github.com/developmentseed/titiler.git

$ pip install -e .
$ uvicorn titiler.main:app --reload
```
Or with Docker
```
$ docker-compose build
$ docker-compose up 
```

# API

### Doc

`:endpoint:/docs`
![](https://user-images.githubusercontent.com/10407788/78325903-011c9680-7547-11ea-853f-50e0fb0f4d92.png)

### Tiles

`:endpoint:/v1/{z}/{x}/{y}[@{scale}x][.{ext}]`
- **z**: Mercator tiles's zoom level.
- **x**: Mercator tiles's column.
- **y**: Mercator tiles's row.
- **scale**: Tile size scale, default is set to 1 (256x256). OPTIONAL
- **ext**: Output image format, default is set to None and will be either JPEG or PNG depending on masked value. OPTIONAL
- **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**
- **bidx**: Coma (',') delimited band indexes. OPTIONAL
- **nodata**: Overwrite internal Nodata value. OPTIONAL
- **rescale**: Coma (',') delimited Min,Max bounds. OPTIONAL
- **color_formula**: rio-color formula. OPTIONAL
- **color_map**: rio-tiler color map name. OPTIONAL

### Metadata

`:endpoint:/v1/tilejson.json` - Get tileJSON document
- **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**
- **tile_format**: Output image format, default is set to None and will be either JPEG or PNG depending on masked value.
- **tile_scale**: Tile size scale, default is set to 1 (256x256). OPTIONAL
- **kwargs**: Other options will be forwarded to the `tiles` url.

`:endpoint:/v1/bounds` - Get general image bounds
- **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**

`:endpoint:/v1/info` - Get general image info
- **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**

`:endpoint:/v1/metadata` - Get image statistics
- **url**: Cloud Optimized GeoTIFF URL. **REQUIRED**
- **bidx**: Coma (',') delimited band indexes. OPTIONAL
- **nodata**: Overwrite internal Nodata value. OPTIONAL
- **pmin**: min percentile, default is 2. OPTIONAL
- **pmax**: max percentile, default is 98. OPTIONAL
- **max_size**: Max image size from which to calculate statistics, default is 1024. OPTIONAL
- **histogram_bins**: Histogram bins, default is 20. OPTIONAL
- **histogram_range**: Coma (',') delimited histogram bounds. OPTIONAL

## UI

`:endpoint:/index.html` - Full UI (histogram, predefined rescaling, ...)

`:endpoint:/simple_viewer.html` - Simple UI (no histogram, manual rescaling, ...)

# Project structure

```
titiler/                         - titiler python module.
 ├── api/                        - general api directory.
 │   ├── api_v1/                 - directory hosting version 1 of the API.
 │   │   ├── endpoints           - api routes.
 │   │   │   ├── metadata.py     - metadata endpoints (e.g. /tilesjson.json, /metadata...).
 │   │   │   ├── ogc.py          - OGC endpoints (e.g WMTS).
 │   │   │   ├── operations.py   - clip/points endpoints.
 │   │   │   ├── tiles.py        - tiling related endpoints.
 │   │   └── api.py              - construct the API by merging api_v1 endpoints.
 │   └── utils.py                - API utility functions.
 │
 ├── core/                       - application configuration.
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
OpenAPI/
 └── openapi.json                - OpenAPI document.

```

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

