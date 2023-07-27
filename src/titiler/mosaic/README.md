## titiler.mosaic

Adds support for MosaicJSON in Titiler.

## Installation

```bash
$ python -m pip install -U pip

# From Pypi
$ python -m pip install titiler.mosaic

# Or from sources
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler && python -m pip install -e src/titiler/core -e src/titiler/mosaic
```

## How To

```python
from fastapi import FastAPI
from titiler.mosaic.factory import MosaicTilerFactory

# Create a FastAPI application
app = FastAPI(
    description="A lightweight Cloud Optimized GeoTIFF tile server",
)

# Create a set of MosaicJSON endpoints
mosaic = MosaicTilerFactory()

# Register the Mosaic endpoints to the application
app.include_router(mosaic.router, tags=["MosaicJSON"])
```

See [titiler.application](../application) for a full example.

## Package structure

```
titiler/
 └── mosaic/
    ├── tests/                   - Tests suite
    └── titiler/mosaic/            - `mosaic` namespace package
        ├── models/
        |   └── responses.py     - mosaic response models
        ├── errors.py            - cogeo-mosaic known errors
        └── factory.py           - Mosaic endpoints factory
```
