## titiler.xarray

Adds support for Xarray Dataset (NetCDF/Zarr) in Titiler.

## Installation

```bash
$ python -m pip install -U pip

# From Pypi
$ python -m pip install titiler.xarray

# Or from sources
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler && python -m pip install -e src/titiler/core -e src/titiler/xarray
```

## How To

```python
from fastapi import FastAPI
from titiler.xarray.factory import TilerFactory

# Create a FastAPI application
app = FastAPI(
    description="A lightweight Cloud Optimized GeoTIFF tile server",
)

# Create a set of MosaicJSON endpoints
endpoint = TilerFactory()

# Register the Mosaic endpoints to the application
app.include_router(endpoint.router)
```

## Package structure

```
titiler/
 └── xarray/
    ├── tests/                   - Tests suite
    └── titiler/xarray/          - `xarray` namespace package
        ├── dependencies.py      - titiler-xarray dependencies
        ├── io.py                - titiler-xarray Readers
        └── factory.py           - endpoints factory
```
