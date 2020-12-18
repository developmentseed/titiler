<p align="center">
  <img src="https://user-images.githubusercontent.com/10407788/84913491-99c3ac80-b088-11ea-846d-75db9e3ab31c.jpg"/>
  <p align="center">A lightweight dynamic tile server.</p>
</p>

<p align="center">
  <a href="https://github.com/developmentseed/titiler/actions?query=workflow%3ACI" target="_blank">
      <img src="https://github.com/developmentseed/titiler/workflows/CI/badge.svg" alt="Test">
  </a>
  <a href="https://codecov.io/gh/developmentseed/titiler" target="_blank">
      <img src="https://codecov.io/gh/developmentseed/titiler/branch/master/graph/badge.svg" alt="Coverage">
  </a>
  <a href="https://pypi.org/project/titiler" target="_blank">
      <img src="https://img.shields.io/pypi/v/titiler?color=%2334D058&label=pypi%20package" alt="Package version">
  </a>
  <a href="https://github.com/developmentseed/titiler/blob/master/LICENSE" target="_blank">
      <img src="https://img.shields.io/github/license/developmentseed/titiler.svg" alt="Downloads">
  </a>
  <a href="https://mybinder.org/v2/gh/developmentseed/titiler/master" target="_blank">
      <img src="https://mybinder.org/badge_logo.svg" alt="Downloads">
  </a>
  <a href="https://hub.docker.com/r/developmentseed/titiler" target="_blank">
      <img src="https://img.shields.io/docker/v/developmentseed/titiler?color=%2334D058&label=docker%20hub" alt="Docker">
  </a>
</p>

---

**Documentation**: <a href="https://devseed.com/titiler/" target="_blank">https://devseed.com/titiler/</a>

**Source Code**: <a href="https://github.com/developmentseed/titiler" target="_blank">https://github.com/developmentseed/titiler</a>

---

`Titiler`, pronounced **tee-tiler** (*ti* is the diminutive version of the french *petit* which means small), is a lightweight application (FastAPI) focused on creating web map tiles dynamically from [Cloud Optimized GeoTIFF](https://cogeo.org), [STAC](https://stacspec.org) or [MosaicJSON](https://github.com/developmentseed/mosaicjson-spec/).

Note: This project is the descendant of [`cogeo-tiler`](https://github.com/developmentseed/cogeo-tiler) and [`cogeo-mosaic-tiler`](https://github.com/developmentseed/cogeo-mosaic-tiler).

## Features

- [Cloud Optimized GeoTIFF](http://www.cogeo.org/) support
- [SpatioTemporal Asset Catalog](https://stacspec.org) support
- Virtual mosaic support (via [MosaicJSON](https://github.com/developmentseed/mosaicjson-spec/))
- Multiple projections (see [TileMatrixSets](https://www.ogc.org/standards/tms)) via [`morecantile`](https://github.com/developmentseed/morecantile).
- JPEG / JP2 / PNG / WEBP / GTIFF / NumpyTile output format support
- OGC WMTS support
- Automatic OpenAPI documentation (FastAPI builtin)
- Example of AWS Lambda / ECS deployment (via CDK)

## Installation

```bash
$ pip install -U pip
# For rio-color, we need to install numpy before installing titiler
$ pip install numpy

# From Pypi
$ pip install titiler["server"]

# Or from sources
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler && pip install -e .["server"]
```

Launch Application
```bash
$ uvicorn titiler.main:app --reload
```

Or with Docker
```
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler

$ export AWS_ACCESS_KEY_ID=...
$ export AWS_SECRET_ACCESS_KEY=...
$ docker-compose build
$ docker-compose up
```

## Docker

Ready to use/deploy images can be found on Docker Hub and AWS public ECR registery.

- Docker Hub: https://hub.docker.com/repository/docker/developmentseed/titiler

```bash
docker run --name titiler \
    -p 8000:8000 \
    --env PORT=8000 \
    --env WORKERS_PER_CORE=1 \
    --rm -it developmentseed/titiler
```

- AWS ECR: https://gallery.ecr.aws/s2n1v5w1/titiler

```bash
docker run --name titiler \
    -p 8000:8000 \
    --env PORT=8000 \
    --env WORKERS_PER_CORE=1 \
    --rm -it public.ecr.aws/s2n1v5w1/titiler
```

Some options can be set via environement variables, see: https://github.com/tiangolo/uvicorn-gunicorn-docker#advanced-usage

## Project structure

```
titiler/                         - titiler python module.
 ├── custom/                     - Custom colormap and TMS grids.
 ├── endpoints                   - API routes.
 │   ├── cog.py                  - COG related endpoints.
 │   ├── stac.py                 - STAC related endpoints.
 │   ├── mosaic.py               - MosaicJSON related endpoints.
 │   ├── factory.py              - TiTiler Router Factories.
 │   └── tms.py                  - TileMatrixSets endpoints.
 ├── models/                     - pydantic models for this application.
 ├── ressources/                 - application resources (enums, constants, etc.).
 ├── templates/                  - html/xml models.
 ├── middleware.py               - Custom Starlette middlewares.
 ├── dependencies.py             - API dependencies.
 ├── errors.py                   - API custom error handling.
 ├── main.py                     - FastAPI application creation and configuration.
 ├── settings.py                 - application configuration.
 ├── utils.py                    - utility functions.
 │
stack/
 ├── app.py                      - AWS Stack definition (vpc, cluster, ecs, alb ...)
 ├── config.py                   - Optional parameters for the stack definition [EDIT THIS]
 │
Dockerfiles/
 ├── Dockerfile                  - Dockerfile to build the ECS service image.
 ├── lambda.package              - Dockerfile to build the Lambda service package.
 ├── lambda.container            - Dockerfile to build the Lambda service container.
 │
lambda/
 │   └── handler.py              - Mangum adaptor for AWS Lambda.
 │
docs/                            - Project documentation.
```

## Contribution & Development

See [CONTRIBUTING.md](https://github.com/developmentseed/titiler/blob/master/CONTRIBUTING.md)

## License

See [LICENSE](https://github.com/developmentseed/titiler/blob/master/LICENSE)

## Authors

Created by [Development Seed](<http://developmentseed.org>)

See [contributors](https://github.com/developmentseed/titiler/graphs/contributors) for a listing of individual contributors.

## Changes

See [CHANGES.md](https://github.com/developmentseed/titiler/blob/master/CHANGES.md).
