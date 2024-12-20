## titiler.xarray

Adds support for Xarray Dataset (NetCDF/Zarr) in Titiler.

## Installation

```bash
python -m pip install -U pip

# From Pypi
python -m pip install "titiler.xarray[full]"

# Or from sources
git clone https://github.com/developmentseed/titiler.git
cd titiler && python -m pip install -e src/titiler/core -e "src/titiler/xarray[full]"
```

#### Installation options

Default installation for `titiler.xarray` DOES NOT include `fsspec` or any storage's specific dependencies (e.g `s3fs`) nor `engine` dependencies (`zarr`, `h5netcdf`). This is to ease the customization and deployment of user's applications. If you want to use the default's dataset reader you will need to at least use the `[minimal]` dependencies (e.g `python -m pip install "titiler.xarray[minimal]"`).

Here is the list of available options:

- **full**: `zarr`, `h5netcdf`,  `fsspec`, `s3fs`, `aiohttp`, `gcsfs`
- **minimal**: `zarr`, `h5netcdf`,  `fsspec`
- **gcs**: `gcsfs`
- **s3**: `s3fs`
- **http**: `aiohttp`

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
        ├── io.py                - titiler-xarray Readers
        └── factory.py           - endpoints factory
```

## Custom Dataset Opener

A default Dataset IO is provided within `titiler.xarray.Reader` class but will require optional dependencies (`fsspec`, `zarr`, `h5netcdf`, ...) to be installed with `python -m pip install "titiler.xarray[full]"`.
Dependencies are optional so the entire package size can be optimized to only include dependencies required by a given application.

Example:

**requirements**:
- `titiler.xarray` (base)
- `h5netcdf`


```python
from typing import Callable
import attr
from fastapi import FastAPI
from titiler.xarray.io import Reader
from titiler.xarray.extensions import VariablesExtension
from titiler.xarray.factory import TilerFactory

import xarray
import h5netcdf  # noqa

# Create a simple Custom reader, using `xarray.open_dataset` opener
@attr.s
class CustomReader(Reader):
    """Custom io.Reader using xarray.open_dataset opener."""
    # xarray.Dataset options
    opener: Callable[..., xarray.Dataset] = attr.ib(default=xarray.open_dataset)


# Create FastAPI application
app = FastAPI(openapi_url="/api", docs_url="/api.html")

# Create custom endpoints with the CustomReader
md = TilerFactory(
    reader=CustomReader,
    router_prefix="/md",
    extensions=[
        # we also want to use the simple opener for the Extension
        VariablesExtension(dataset_opener=xarray.open_dataset),
    ],
)

app.include_router(md.router, prefix="/md", tags=["Multi Dimensional"])
```
