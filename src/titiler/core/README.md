## titiler.core

Core of Titiler's application. Contains blocks to create dynamic tile servers.

## Installation

```bash
$ pip install -U pip

# From Pypi
$ pip install titiler.core

# Or from sources
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler && pip install -e titiler/core
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
        ├── models/
        |   ├── cogeo.py         - rio-cogeo pydantic models
        |   ├── mapbox.py        - Mapbox TileJSON pydantic model
        |   └── OGC.py           - Open GeoSpatial Consortium pydantic models (TileMatrixSets...)
        ├── resources/
        |   ├── enums.py         - Titiler's enumerations (e.g MediaType)
        |   └── responses.py     - Custom Starlette's responses
        ├── templates/
        |   └── wmts.xml         - OGC WMTS template
        ├── dependencies.py      - Titiler FastAPI's dependencies
        ├── errors.py            - Errors handler factory
        ├── factory.py           - Dynamic tiler endpoints factories
        ├── routing.py           - Custom APIRoute class
        ├── utils.py             - Titiler utility functions
        └── version.py           - version
```
