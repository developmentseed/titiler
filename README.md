<p align="center">
  <img src="https://user-images.githubusercontent.com/10407788/84913491-99c3ac80-b088-11ea-846d-75db9e3ab31c.jpg"/>
  <p align="center">A lightweight Cloud Optimized GeoTIFF dynamic tile server.</p>
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
</p>

---

**Documentation**: <a href="https://devseed.com/titiler/" target="_blank">https://devseed.com/titiler/</a>

**Source Code**: <a href="https://github.com/developmentseed/titiler" target="_blank">https://github.com/developmentseed/titiler</a>

---

Titiler, pronounced **tee-tiler** (*ti* is the diminutive version of the french *petit* which means small), is a lightweight server to create map tiles dynamically from Cloud Optimized GeoTIFF ([COG](https://cogeo.org)).

This project is the descendant of [`cogeo-tiler`](https://github.com/developmentseed/cogeo-tiler) and [`cogeo-mosaic-tiler`](https://github.com/developmentseed/cogeo-mosaic-tiler).

## Features

- Multiple TileMatrixSets via [`morecantile`](https://github.com/developmentseed/morecantile). By default, output map tiles are in the standard Web Mercator projection used by most mapping libraries, but [support for alternative projections](/docs/TMS.md) is available.
- [Cloud Optimized GeoTIFF](http://www.cogeo.org/) support
- [SpatioTemporal Asset Catalog](https://stacspec.org) support
- Mosaic support (via [MosaicJSON](https://github.com/developmentseed/mosaicjson-spec/))
- OGC WMTS support
- AWS Lambda / ECS deployment options

## Installation

```bash
$ pip install -U pip
$ pip install titiler["server"]

# Or from sources
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler && pip install -e .["server"]
```

Launch Application
```
$ pip install -e .
$ uvicorn titiler.main:app --reload
```

Or with Docker
```
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler

$ docker-compose build
$ docker-compose up
```

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
 ├── ecs/
 │   └── Dockerfile              - Dockerfile to build the ECS service image.
 ├── lambda/
 │   └── Dockerfile              - Dockerfile to build the Lambda service image.
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

## Changes

See [CHANGES.md](https://github.com/developmentseed/titiler/blob/master/CHANGES.md).
