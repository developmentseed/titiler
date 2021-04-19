<p align="center">
  <img src="https://user-images.githubusercontent.com/10407788/84913491-99c3ac80-b088-11ea-846d-75db9e3ab31c.jpg"/>
  <p align="center">A modern dynamic tile server built on top of FastAPI and Rasterio/GDAL.</p>
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

`Titiler`, pronounced **tee-tiler** (*ti* is the diminutive version of the french *petit* which means small), is a set of python modules that focus on creating FastAPI application for dynamic tiling.

Note: This project is the descendant of [`cogeo-tiler`](https://github.com/developmentseed/cogeo-tiler) and [`cogeo-mosaic-tiler`](https://github.com/developmentseed/cogeo-mosaic-tiler).

## Features

- Built on top of [FastAPI](https://fastapi.tiangolo.com)
- [Cloud Optimized GeoTIFF](http://www.cogeo.org/) support
- [SpatioTemporal Asset Catalog](https://stacspec.org) support
- Multiple projections support (see [TileMatrixSets](https://www.ogc.org/standards/tms)) via [`morecantile`](https://github.com/developmentseed/morecantile).
- JPEG / JP2 / PNG / WEBP / GTIFF / NumpyTile output format support
- OGC WMTS support
- Automatic OpenAPI documentation (FastAPI builtin)
- Virtual mosaic support (via [MosaicJSON](https://github.com/developmentseed/mosaicjson-spec/))
- Example of AWS Lambda / ECS deployment (via CDK)

## Packages

Starting with version `0.3.0`, the `TiTiler` python module has been splitted into a set of python namespace packages: `titiler.{package}`.

- [**titiler.core**](https://github.com/developmentseed/titiler/tree/master/titiler/core)

    The `Core` package contains libraries to help creating dynamic tiler for COG and STAC.

- [**titiler.mosaic**](https://github.com/developmentseed/titiler/tree/master/titiler/mosaic)

    The `mosaic` package contains libraries to help creating dynamic tiler for MosaicJSON (adds `cogeo-mosaic` requirement).

- [**titiler.application**](https://github.com/developmentseed/titiler/tree/master/titiler/application)

    TiTiler's `demo` package. Contains a FastAPI application with full support of COG, STAC and MosaicJSON.

## Installation

```bash
$ pip install -U pip

# From Pypi
$ pip install titiler.{package}
# e.g
# pip install titiler.core
# pip install titiler.mosaic
# pip install titiler.application

# Or from sources
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler && pip install -e titiler/core titiler/mosaic titiler/application
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

- AWS ECR: https://gallery.ecr.aws/developmentseed/titiler

```bash
docker run --name titiler \
    -p 8000:8000 \
    --env PORT=8000 \
    --env WORKERS_PER_CORE=1 \
    --rm -it public.ecr.aws/developmentseed/titiler
```

- Built the docker locally
```
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler

$ export AWS_ACCESS_KEY_ID=...
$ export AWS_SECRET_ACCESS_KEY=...
$ docker-compose build
$ docker-compose up
```

Some options can be set via environment variables, see: https://github.com/tiangolo/uvicorn-gunicorn-docker#advanced-usage

## Project structure

```
titiler/                         - titiler modules.
 ├── application/                - Titiler's `Application` package
 ├── core/                       - Titiler's `Core` package
 └── mosaic/                     - Titiler's `Mosaic` package
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
