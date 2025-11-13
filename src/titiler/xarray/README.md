## titiler.xarray

Adds support for Xarray Dataset (NetCDF/Zarr) in Titiler.

## Installation

```bash
python -m pip install -U pip

# From Pypi
python -m pip install "titiler.xarray[full]"

# Or from sources
git clone https://github.com/developmentseed/titiler.git
cd titiler && python -m pip install -e src/titiler/core -e "src/titiler/xarray"
```

#### Installation options

Default installation for `titiler.xarray` DOES NOT include `fsspec` or any storage's specific dependencies (e.g `s3fs`) nor `engine` dependencies (`zarr`, `h5netcdf`). This is to ease the customization and deployment of user's applications. If you want to use the default's dataset reader you will need to at least use the `[minimal]` dependencies (e.g `python -m pip install "titiler.xarray[minimal]"`).

Here is the list of available options:

- **fs**: `h5netcdf`,  `fsspec`, `s3fs`, `aiohttp`, `gcsfs`

#### Dependencies

Titiler.xarray follows [SPEC 0](https://scientific-python.org/specs/spec-0000/), similar to [xarray](https://docs.xarray.dev/en/v2025.09.0/getting-started-guide/installing.html#minimum-dependency-versions).

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
        ├── extensions.py        - titiler-xarray extensions
        ├── main.py              - main fastapi application
        ├── io.py                - titiler-xarray Readers
        └── factory.py           - endpoints factory
```

## Custom Dataset Opener

A default Dataset IO is provided within `titiler.xarray.io.Reader` class with only support for Zarr dataset (via xarray+zarr-python). 

For other dataset (e.g NetCDF), you can use `titiler.xarray.io.FsReader` which use the optional dependencies (`fsspec`, `netcdf5`).

```
python -m pip install "titiler.xarray[fs]"
```

Example of application with `fsspec` reader:

```python
from fastapi import FastAPI
from titiler.xarray.extensions import VariablesExtension
from titiler.xarray.factory import TilerFactory
from titiler.xarray.io import FsReader

# Create FastAPI application
app = FastAPI(openapi_url="/api", docs_url="/api.html")

# Create custom endpoints with the FsReader
md = TilerFactory(
    reader=FsReader,
    router_prefix="/md",
    extensions=[
        # we also want to use the simple opener for the Extension
        VariablesExtension(dataset_opener=xarray.open_dataset),
    ],
)

app.include_router(md.router, prefix="/md", tags=["Multi Dimensional"])
```
