"""titiler xarray app."""

from fastapi import FastAPI

from titiler.xarray.extensions import VariablesExtension
from titiler.xarray.factory import TilerFactory

###############################################################################

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

app.include_router(
    md.router,
    prefix="/md",
    tags=["Multi Dimensional"],
)
