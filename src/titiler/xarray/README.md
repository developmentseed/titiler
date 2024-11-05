## titiler.xarray

Adds support for Xarray Dataset (NetCDF/Zarr) in Titiler.

## Installation

```bash
$ python -m pip install -U pip

# From Pypi
$ python -m pip install "titiler.xarray[all]"

# Or from sources
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler && python -m pip install -e src/titiler/core -e "src/titiler/xarray[all]"
```

## How To

```python
from fastapi import FastAPI

from titiler.xarray.extensions import VariablesExtension
from titiler.xarray.factory import TilerFactory

app = FastAPI(
    openapi_url="/api",
    docs_url="/api.html",
    description="""Xarray based tiles server for MultiDimensional dataset (Zarr/NetCDF).

---

**Documentation**: <a href="https://developmentseed.org/titiler/" target="_blank">https://developmentseed.org/titiler/</a>

**Source Code**: <a href="https://github.com/developmentseed/titiler" target="_blank">https://github.com/developmentseed/titiler</a>

---
    """,
)

md = TilerFactory(
    router_prefix="/md",
    extensions=[
        VariablesExtension(),
    ],
)
app.include_router(md.router, prefix="/md", tags=["Multi Dimensional"])
```

## Package structure

```
titiler/
 └── xarray/
    ├── tests/                   - Tests suite
    └── titiler/xarray/          - `xarray` namespace package
        ├── dependencies.py      - titiler-xarray dependencies
        ├── extentions.py        - titiler-xarray extensions
        ├── io.py                - titiler-xarray Readers
        └── factory.py           - endpoints factory
```

## Custom Dataset Opener

A default Dataset IO is provided within `titiler.xarray.Reader` class but will require optional dependencies (fsspec, zarr, h5netcdf, ...) to be installed with `python -m pip install "titiler.xarray[all]"`.
Dependencies are optional so the entire package size can be optimized to only include dependencies required by a given application.

```python
from titiler.xarray.io import Reader

import xarray
import h5netcdf  # noqa

with Reader(
    "tests/fixtures/dataset_2d.nc",
    "dataset",
    opener=xarray.open_dataset,
) as src:
    print(src.ds)

>>> <xarray.Dataset> Size: 16MB
Dimensions:  (x: 2000, y: 1000)
Coordinates:
  * x        (x) float64 16kB -170.0 -169.8 -169.7 -169.5 ... 169.5 169.7 169.8
  * y        (y) float64 8kB -80.0 -79.84 -79.68 -79.52 ... 79.52 79.68 79.84
Data variables:
    dataset  (y, x) float64 16MB ...
```
