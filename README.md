# titiler

A lightweight Cloud Optimized GeoTIFF dynamic tile server.

[![CircleCI](https://circleci.com/gh/developmentseed/titiler.svg?style=svg)](https://circleci.com/gh/developmentseed/titiler)
[![codecov](https://codecov.io/gh/developmentseed/titiler/branch/master/graph/badge.svg)](https://codecov.io/gh/developmentseed/titiler)

Titiler, pronounced **tee-tiler** (*ti* is the diminutive version of the french *petit* which means small), is lightweight service, which sole goal is to create map tiles dynamically from Cloud Optimized GeoTIFF [COG](cogeo.org).

This project is the descendant of https://github.com/developmentseed/cogeo-tiler

## Features

- Multiple TileMatrixSets via [morecantile](https://github.com/developmentseed/morecantile). Default is set to WebMercatorQuad which is the usual Web Mercator projection used in most of Wep Map libraries.)
- Cloud Optimized GeoTIFF support
- SpatioTemporal Asset Catalog support (Optional)
- OGC WMTS support
- Caching layer for tiles (Optional)
- AWS Lambda / ECS deployement options

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

### Installation options
 
- STAC: `pip install -e .["stac"]`


# Docs

[link](docs/README.md)


# Deployment

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
docs/                            - Project documentations.

```

# Contribution & Development

Issues and pull requests are more than welcome.

**dev install**

```bash
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler
$ pip install -e .[dev]
```

**Python3.7 only**

This repo is set to use `pre-commit` to run *isort*, *mypy*, *flake8*, *pydocstring* and *black* ("uncompromising Python code formatter") when commiting new code.

```bash
$ pre-commit install
```

## Authors
Created by [Development Seed](<http://developmentseed.org>)

