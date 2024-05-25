
`TiTiler` is designed to help user customize input/output for each endpoint. This section goes over some simple customization examples.

### Custom Colormap

Add user defined colormap to the default colormaps provided by rio-tiler

```python
from fastapi import FastAPI

from rio_tiler.colormap import cmap as default_cmap

from titiler.core.dependencies import create_colormap_dependency
from titiler.core.factory import TilerFactory


app = FastAPI(title="My simple app with custom TMS")

cmap_values = {
    "cmap1": {6: (4, 5, 6, 255)},
}
# add custom colormap `cmap1` to the default colormaps
cmap = default_cmap.register(cmap_values)
ColorMapParams = create_colormap_dependency(cmap)


cog = TilerFactory(colormap_dependency=ColorMapParams)
app.include_router(cog.router)
```

### Custom DatasetPathParams for `reader_dependency`

One common customization could be to create your own `path_dependency`. This dependency is used on all endpoint and pass inputs to the *Readers* (MosaicBackend, COGReader, STACReader...).

Here an example which allow a mosaic to be passed by a `mosaic name` instead of a full S3 url.

```python
import os
import re

from fastapi import FastAPI, HTTPException, Query

from titiler.mosaic.factory import MosaicTilerFactory


MOSAIC_BACKEND = os.getenv("TITILER_MOSAIC_BACKEND")
MOSAIC_HOST = os.getenv("TITILER_MOSAIC_HOST")


def MosaicPathParams(
    mosaic: str = Query(..., description="mosaic name")
) -> str:
    """Create dataset path from args"""
    # mosaic name should be in form of `{user}.{layername}`
    if not re.match(self.mosaic, r"^[a-zA-Z0-9-_]{1,32}\.[a-zA-Z0-9-_]{1,32}$"):
        raise HTTPException(
            status_code=400,
                detail=f"Invalid mosaic name {self.input}.",
            )

        return f"{MOSAIC_BACKEND}{MOSAIC_HOST}/{self.input}.json.gz"


app = FastAPI()
mosaic = MosaicTilerFactory(path_dependency=MosaicPathParams)
app.include_router(mosaic.router)
```

The endpoint url will now look like: `{endpoint}/mosaic/tilejson.json?mosaic=vincent.mosaic`


### Custom TMS

```python
from morecantile import tms, TileMatrixSet
from pyproj import CRS

from titiler.core.factory import TilerFactory

# 1. Create Custom TMS
EPSG6933 = TileMatrixSet.custom(
    (-17357881.81713629, -7324184.56362408, 17357881.81713629, 7324184.56362408),
    CRS.from_epsg(6933),
    identifier="EPSG6933",
    matrix_scale=[1, 1],
)

# 2. Register TMS
tms = tms.register([EPSG6933])

# 3. Create Tiler
COGTilerWithCustomTMS = TilerFactory(supported_tms=tms)
```

### Add a MosaicJSON creation endpoint
```python

from dataclasses import dataclass
from typing import List, Optional

from titiler.mosaic.factory import MosaicTilerFactory
from titiler.core.errors import BadRequestError
from cogeo_mosaic.mosaic import MosaicJSON
from cogeo_mosaic.utils import get_footprints
import rasterio

from pydantic import BaseModel


# Models from POST/PUT Body
class CreateMosaicJSON(BaseModel):
    """Request body for MosaicJSON creation"""

    files: List[str]              # Files to add to the mosaic
    url: str                      # path where to save the mosaicJSON
    minzoom: Optional[int] = None
    maxzoom: Optional[int] = None
    max_threads: int = 20
    overwrite: bool = False


class UpdateMosaicJSON(BaseModel):
    """Request body for updating an existing MosaicJSON"""

    files: List[str]              # Files to add to the mosaic
    url: str                      # path where to save the mosaicJSON
    max_threads: int = 20
    add_first: bool = True


@dataclass
class CustomMosaicFactory(MosaicTilerFactory):

    def register_routes(self):
        """Update the class method to add create/update"""
        super().register_routes()
        # new methods/endpoint
        self.create()
        self.update()

    def create(self):
        """Register / (POST) Create endpoint."""

        @self.router.post(
            "", response_model=MosaicJSON, response_model_exclude_none=True
        )
        def create(
            body: CreateMosaicJSON,
            env=Depends(self.environment_dependency),
        ):
            """Create a MosaicJSON"""
            # Write can write to either a local path, a S3 path...
            # See https://developmentseed.org/cogeo-mosaic/advanced/backends/ for the list of supported backends

            # Create a MosaicJSON file from a list of URL
            mosaic = MosaicJSON.from_urls(
                body.files,
                minzoom=body.minzoom,
                maxzoom=body.maxzoom,
                max_threads=body.max_threads,
            )

            # Write the MosaicJSON using a cogeo-mosaic backend
            with rasterio.Env(**env):
                with self.reader(
                    body.url, mosaic_def=mosaic, reader=self.dataset_reader
                ) as mosaic:
                    try:
                        mosaic.write(overwrite=body.overwrite)
                    except NotImplementedError:
                        raise BadRequestError(
                            f"{mosaic.__class__.__name__} does not support write operations"
                        )
                    return mosaic.mosaic_def

    def update(self):
        """Register / (PUST) Update endpoint."""

        @self.router.put(
            "", response_model=MosaicJSON, response_model_exclude_none=True
        )
        def update_mosaicjson(
            body: UpdateMosaicJSON,
            env=Depends(self.environment_dependency),
        ):
            """Update an existing MosaicJSON"""
            with rasterio.Env(**env):
                with self.reader(body.url, reader=self.dataset_reader) as mosaic:
                    features = get_footprints(body.files, max_threads=body.max_threads)
                    try:
                        mosaic.update(features, add_first=body.add_first, quiet=True)
                    except NotImplementedError:
                        raise BadRequestError(
                            f"{mosaic.__class__.__name__} does not support update operations"
                        )
                    return mosaic.mosaic_def

```
