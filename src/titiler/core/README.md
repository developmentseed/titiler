## titiler.core

Core of Titiler's application. Contains blocks to create dynamic tile servers.

## Installation

```bash
$ python -m pip install -U pip

# From Pypi
$ python -m pip install titiler.core

# Or from sources
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler && python -m pip install -e src/titiler/core
```

## How To

```python
from fastapi import FastAPI
from titiler.core.factory import TilerFactory

# Create a FastAPI application
app = FastAPI(
    description="A lightweight Cloud Optimized GeoTIFF tile server",
)

# Create a set of COG endpoints
cog = TilerFactory()

# Register the COG endpoints to the application
app.include_router(cog.router, tags=["Cloud Optimized GeoTIFF"])
```

See [titiler.application](../application) for a full example.

## Package structure

```
titiler/
 └── core/
    ├── tests/                   - Tests suite
    └── titiler/core/            - `core` namespace package
        ├── algorithm/
        |   ├── base.py          - ABC Base Class for custom algorithms
        |   ├── dem.py           - Elevation data related algorithms
        |   └── index.py         - Simple band index algorithms
        ├── models/
        |   ├── response.py      - Titiler's response models
        |   ├── mapbox.py        - Mapbox TileJSON pydantic model
        |   └── OGC.py           - Open GeoSpatial Consortium pydantic models (TileMatrixSets...)
        ├── resources/
        |   ├── enums.py         - Titiler's enumerations (e.g MediaType)
        |   └── responses.py     - Custom Starlette's responses
        ├── templates/
        |   ├── map.html         - Simple Map viewer (built with leaflet)
        |   └── wmts.xml         - OGC WMTS document template
        ├── dependencies.py      - Titiler FastAPI's dependencies
        ├── errors.py            - Errors handler factory
        ├── middleware.py        - Starlette middlewares
        ├── factory.py           - Dynamic tiler endpoints factories
        ├── routing.py           - Custom APIRoute class
        └── utils.py             - Titiler utility functions
```
