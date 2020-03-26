# titiler

A lightweight Cloud Optimized GeoTIFF tile server.

[![CircleCI](https://circleci.com/gh/developmentseed/titiler.svg?style=svg)](https://circleci.com/gh/developmentseed/rio-tiler)
[![codecov](https://codecov.io/gh/developmentseed/titiler/branch/master/graph/badge.svg)](https://codecov.io/gh/developmentseed/titiler)

# Deployment

**To Do**

# Test locally
```bash
$ uvicorn titiler.main:app --reload
```

### Docker
```
$ docker-compose build
$ docker-compose up 
```

## Authors
Created by [Development Seed](<http://developmentseed.org>)


## Project structure

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
 └── utils.py                    - utility functions.
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
