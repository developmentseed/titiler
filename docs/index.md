# titiler

<p align="center">
  <img src="https://user-images.githubusercontent.com/10407788/84913491-99c3ac80-b088-11ea-846d-75db9e3ab31c.jpg"/>
  <p align="center">A lightweight Cloud Optimized GeoTIFF dynamic tile server.</p>
</p>

<p align="center">
  <a href="https://circleci.com/gh/developmentseed/titiler" target="_blank">
      <img src="https://circleci.com/gh/developmentseed/titiler.svg?style=svg" alt="Test">
  </a>
  <a href="https://codecov.io/gh/developmentseed/titiler" target="_blank">
      <img src="https://codecov.io/gh/developmentseed/titiler/branch/master/graph/badge.svg" alt="Coverage">
  </a>
  <a href="https://github.com/developmentseed/titiler/blob/master/LICENSE" target="_blank">
      <img src="https://img.shields.io/github/license/developmentseed/titiler.svg" alt="Downloads">
  </a>
</p>

Titiler, pronounced **tee-tiler** (*ti* is the diminutive version of the french *petit* which means small), is lightweight service, which sole goal is to create map tiles dynamically from Cloud Optimized GeoTIFF [COG](cogeo.org).

This project is the descendant of https://github.com/developmentseed/cogeo-tiler

## Features

- Multiple TileMatrixSets via [morecantile](https://github.com/developmentseed/morecantile). Default is set to WebMercatorQuad which is the usual Web Mercator projection used in most of Wep Map libraries.) (see [docs/TMS](/docs/TMS.md))
- Cloud Optimized GeoTIFF support (see [docs/COG](/docs/COG.md))
- SpatioTemporal Asset Catalog support (see [docs/STAC](/docs/STAC.md))
- MosaicJSON support (Optional)
- OGC WMTS support
- Caching layer for tiles (Optional)
- AWS Lambda / ECS deployement options

## Installation
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