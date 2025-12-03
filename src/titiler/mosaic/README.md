## titiler.mosaic

<img style="max-width:400px" src="https://github.com/user-attachments/assets/14b92588-14eb-4b37-b862-cc5d0d8015c9"/>

Adds support for Mosaic in Titiler. `Mosaic's` backend needs to be built on top of rio-tiler's Mosaic Backend https://cogeotiff.github.io/rio-tiler/advanced/mosaic_backend/

## Installation

```bash
python -m pip install -U pip

# From Pypi
python -m pip install titiler.mosaic

# Or from sources
git clone https://github.com/developmentseed/titiler.git
cd titiler && python -m pip install -e src/titiler/core -e src/titiler/mosaic

# install cogeo-mosaic for MosaicJSON support
python -m pip install cogeo-mosaic
```

## How To

```python
from fastapi import FastAPI
from titiler.mosaic.factory import MosaicTilerFactory

from cogeo_mosaic.backends import MosaicBackend

# Create a FastAPI application
app = FastAPI(
    description="A Mosaic tile server",
)

# Create a set of Mosaic endpoints using MosaicJSON backend from cogeo-mosaic project
mosaic = MosaicTilerFactory(backend=MosaicBackend)

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
        ├── errors.py            - mosaic known errors
        ├── extensions.py        - extensions
        └── factory.py           - Mosaic endpoints factory
```
