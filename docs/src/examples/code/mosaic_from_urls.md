
**Goal**: Create a custom mosaic tiler which takes multiple URL as input

**requirements**: titiler.core | titiler.mosaic


1 - Create a custom Mosaic Backends

```python
"""mosaic backends.

The goal is to build a minimalist Mosaic Backend which takes COG paths as input.

>>> with MultiFilesBackend(["cog1.tif", "cog2.tif"]) as mosaic:
    img = mosaic.tile(1, 1, 1)

app/backends.py

"""
from typing import Type, List, Tuple, Dict, Union

import attr
from rio_tiler.io import BaseReader, COGReader, MultiBandReader, MultiBaseReader
from rio_tiler.constants import WEB_MERCATOR_TMS, WGS84_CRS
from rasterio.crs import CRS
from morecantile import TileMatrixSet

from cogeo_mosaic.backends.base import BaseBackend
from cogeo_mosaic.mosaic import MosaicJSON


@attr.s
class MultiFilesBackend(BaseBackend):

    input: List[str] = attr.ib()

    reader: Union[
        Type[BaseReader],
        Type[MultiBaseReader],
        Type[MultiBandReader],
    ] = attr.ib(default=COGReader)
    reader_options: Dict = attr.ib(factory=dict)

    geographic_crs: CRS = attr.ib(default=WGS84_CRS)

    tms: TileMatrixSet = attr.ib(default=WEB_MERCATOR_TMS)
    minzoom: int = attr.ib(default=0)
    maxzoom: int = attr.ib(default=30)

    # default values for bounds
    bounds: Tuple[float, float, float, float] = attr.ib(
        default=(-180, -90, 180, 90)
    )
    crs: CRS = attr.ib(init=False, default=WGS84_CRS)

    # mosaic_def is outside the __init__ method
    mosaic_def: MosaicJSON = attr.ib(init=False)

    _backend_name = "MultiFiles"

    def __attrs_post_init__(self):
        """Post Init."""
        # Construct a FAKE/Empty mosaicJSON
        # mosaic_def has to be defined.
        self.mosaic_def = MosaicJSON(
            mosaicjson="0.0.2",
            name="it's fake but it's ok",
            minzoom=self.minzoom,
            maxzoom=self.maxzoom,
            tiles=[]  # we set `tiles` to an empty list.
        )

    def write(self, overwrite: bool = True):
        """This method is not used but is required by the abstract class."""
        pass

    def update(self):
        """We overwrite the default method."""
        pass

    def _read(self) -> MosaicJSON:
        """This method is not used but is required by the abstract class."""
        pass

    def assets_for_tile(self, x: int, y: int, z: int) -> List[str]:
        """Retrieve assets for tile."""
        return self.get_assets()

    def assets_for_point(self, lng: float, lat: float) -> List[str]:
        """Retrieve assets for point."""
        return self.get_assets()

    def get_assets(self) -> List[str]:
        """assets are just files we give in path"""
        return self.input

    @property
    def _quadkeys(self) -> List[str]:
        return []

```

2 - Create endpoints

```python
"""routes.

app/routers.py

"""

from dataclasses import dataclass
from typing import List

from titiler.mosaic.factory import MosaicTilerFactory
from fastapi import Query

from .backends import MultiFilesBackend

@dataclass
class MosaicTiler(MosaicTilerFactory):
    """Custom MosaicTilerFactory.

    Note this is a really simple MosaicTiler Factory with only few endpoints.
    """

    def register_routes(self):
        """This Method register routes to the router. """

        self.tile()
        self.tilejson()


def DatasetPathParams(url: str = Query(..., description="Dataset URL")) -> List[str]:
    """Create dataset path from args"""
    return url.split(",")


mosaic = MosaicTiler(reader=MultiFilesBackend, path_dependency=DatasetPathParams)

```

3 - Create app and register our custom endpoints

```python
"""app.

app/main.py

"""

from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.mosaic.errors import MOSAIC_STATUS_CODES

from fastapi import FastAPI

from .routers import mosaic

app = FastAPI()
app.include_router(mosaic.router)
add_exception_handlers(app, DEFAULT_STATUS_CODES)
add_exception_handlers(app, MOSAIC_STATUS_CODES)

```

4. Run and Use

```
$ uvicorn app:app --reload

$ curl http://127.0.0.1:8000/tilejson.json?url=cog1.tif,cog2.tif
```

**Gotcha**

- bounds of the mosaic backend is set to `[-180, -90, 180, 90]`
- minzoom is set to 0
- maxzoom is set to 30
