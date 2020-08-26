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
  <a href="https://github.com/developmentseed/titiler/blob/master/LICENSE" target="_blank">
      <img src="https://img.shields.io/github/license/developmentseed/titiler.svg" alt="Downloads">
  </a>
</p>

---

**Documentation**: <a href="https://devseed.com/titiler/" target="_blank">https://devseed.com/titiler/</a>

**Source Code**: <a href="https://github.com/developmentseed/titiler" target="_blank">https://github.com/developmentseed/titiler</a>

---

Titiler, pronounced **tee-tiler** (*ti* is the diminutive version of the french *petit* which means small), is lightweight service, which sole goal is to create map tiles dynamically from Cloud Optimized GeoTIFF [COG](cogeo.org).

This project is the descendant of [https://github.com/developmentseed/cogeo-tiler](https://github.com/developmentseed/cogeo-tiler)


## Features

- Multiple TileMatrixSets via [morecantile](https://github.com/developmentseed/morecantile). Default is set to WebMercatorQuad which is the usual Web Mercator projection used in most of Wep Map libraries.) (see [docs/TMS](/docs/TMS.md))
- Cloud Optimized GeoTIFF support
- SpatioTemporal Asset Catalog support
- MosaicJSON support
- OGC WMTS support
- Caching layer for tiles (Optional)
- AWS Lambda / ECS deployement options

## Installation

```bash
$ git clone https://github.com/developmentseed/titiler.git

# Install titiler dependencies and uvicorn (local web server)
$ cd titiler && pip install -e .["server"]

$ pip install -U pip
$ pip install -e .
$ uvicorn titiler.main:app --reload
```

Or with Docker
```
$ docker-compose build
$ docker-compose up 
```

## Project structure

```
titiler/                         - titiler python module.
 ├── custom/                     - Custom colormap and TMS grids.
 ├── db/                         - db related stuff.
 ├── endpoints                   - api routes.
 │   ├── cog.py                  - COG related endpoints.
 │   ├── stac.py                 - STAC related endpoints.
 │   ├── mosaic.py               - MosaicJSON related endpoints.
 │   ├── factory.py              - TiTiler Router Factories.
 │   └── tms.py                  - TileMatrixSets endpoints.
 ├── models/                     - pydantic models for this application.
 ├── ressources/                 - application ressources (enums, constants, ...).
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
 │   └── handler.py              - Mangum adaptator fro AWS Lambda.
 │
docs/                            - Project documentations.
```

## Contribution & Development

See [CONTRIBUTING.md](https://github.com/developmentseed/titiler/blob/master/CONTRIBUTING.md)

## License

See [LICENSE](https://github.com/developmentseed/titiler/blob/master/LICENSE)

## Authors

Created by [Development Seed](<http://developmentseed.org>)

## Changes

See [CHANGES.md](https://github.com/developmentseed/titiler/blob/master/CHANGES.md).
