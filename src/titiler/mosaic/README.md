## titiler.mosaic

<img style="max-width:400px" src="https://github.com/user-attachments/assets/14b92588-14eb-4b37-b862-cc5d0d8015c9"/>

Adds support for [MosaicJSON](https://github.com/developmentseed/mosaicjson-spec) in Titiler.

> MosaicJSON is an open standard for representing metadata about a mosaic of Cloud-Optimized GeoTIFF (COG) files.

Ref: https://github.com/developmentseed/mosaicjson-spec

## Installation

```bash
python -m pip install -U pip

# From Pypi
python -m pip install titiler.mosaic

# Or from sources
git clone https://github.com/developmentseed/titiler.git
cd titiler && python -m pip install -e src/titiler/core -e src/titiler/mosaic
```

## How To

```python
from fastapi import FastAPI
from titiler.mosaic.factory import MosaicTilerFactory

# Create a FastAPI application
app = FastAPI(
    description="A Mosaic tile server",
)

# Create a set of MosaicJSON endpoints
mosaic = MosaicTilerFactory()

# Register the Mosaic endpoints to the application
app.include_router(mosaic.router, tags=["MosaicJSON"])
```

## Package structure

```
titiler/
 └── mosaic/
    ├── tests/                   - Tests suite
    └── titiler/mosaic/          - `mosaic` namespace package
        ├── models/
        |   └── responses.py     - mosaic response models
        ├── errors.py            - cogeo-mosaic known errors
        └── factory.py           - Mosaic endpoints factory
```
