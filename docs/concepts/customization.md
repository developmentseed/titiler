
### Example of STAC Tiler

While a STAC tiler is included in the default TiTiler application, it provides
an illustrative example of why one might need a custom tiler. The default
factories create endpoints that expect basic input like `indexes=[1, 2, 3]` and
`resampling_method='nearest'` but STAC needs more info. The STAC reader provided
by `rio-tiler` and `rio-tiler-crs` needs an `assets=` option to specify which
STAC asset(s) you want to read.

We can add additional dependencies to endpoint by using the `additional_dependency` options when creating the factory.

```python
from titiler.endpoints.factory import TMSTilerFactory
from rio_tiler_crs import STACReader
from titiler.dependencies import AssetsParams

stac = TMSTilerFactory(reader=STACReader, additional_dependency=AssetsParams, router_prefix="stac")
```

In :point_up:, the `AssetsParams` will add an `assets` option to each endpoint.

While this is good, it's not enough. STACTiler `metadata()` and `info()` methods return a slightly different output that the usual COGReader (because of multiple assets). We then need to customize a bit more the tiler:

```python
from titiler.endpoint.factory import TMSTilerFactory
from titiler.dependencies import AssetsParams
from titiler.models.cog import cogInfo, cogMetadata


# We create a Sub-Class from the TMSTilerFactory and update 2 methods.
@dataclass
class STACTiler(TMSTilerFactory):
    """Custom Tiler Class for STAC."""

    reader: Type[STACReader] = STACReader  # We set the Reader to STACReader by default
    additional_dependency: Type[AssetsParams] = AssetsParams  # We add the AssetsParams dependency byt default

    # Overwrite _info method to return the list of assets when no assets is passed.
    # 2 changes from the _info in the original factory:
    # - response_model:
    #    response_model=cogInfo -> response_model=Union[List[str], Dict[str, cogInfo]]
    #    The output of STACTiler.info is a dict in form of {"asset1": {`cogIngo`}}
    # - Return list of assets if no `assets` option passed
    #    This can be usefull in case we don't know the assets present in the STAC item.
    def _info(self):
        """Register /info endpoint to router."""

        @self.router.get(
            "/info",
            response_model=Union[List[str], Dict[str, cogInfo]],
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={200: {"description": "Return dataset's basic info."}},
            name=f"{self.router_prefix}info",
        )
        def info(
            src_path=Depends(self.path_dependency),
            options=Depends(self.additional_dependency),
        ):
            """Return basic info."""
            reader = src_path.reader or self.reader
            with reader(src_path.url, **self.reader_options) as src_dst:
                if not options.kwargs.get("assets"):
                    return src_dst.assets
                info = src_dst.info(**options.kwargs)
            return info

    # Overwrite _metadata method because the STACTiler output model is different
    # response_model=cogMetadata -> response_model=Dict[str, cogMetadata]
    # Same as for _info(), we update the output model to match the output result from STACTiler.metadata
    def _metadata(self):
        """Register /metadata endpoint to router."""

        @self.router.get(
            "/metadata",
            response_model=Dict[str, cogMetadata],
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={200: {"description": "Return dataset's metadata."}},
            name=f"{self.router_prefix}metadata",
        )
        def metadata(
            src_path=Depends(self.path_dependency),
            params=Depends(self.metadata_dependency),
            options=Depends(self.additional_dependency),
        ):
            """Return metadata."""
            reader = src_path.reader or self.reader
            with reader(src_path.url, **self.reader_options) as src_dst:
                kwargs = options.kwargs.copy()
                if params.nodata is not None:
                    kwargs["nodata"] = params.nodata
                info = src_dst.metadata(
                    params.pmin,
                    params.pmax,
                    indexes=params.indexes,
                    max_size=params.max_size,
                    hist_options=params.hist_options,
                    bounds=params.bounds,
                    resampling_method=params.resampling_method.name,
                    **kwargs,
                )
            return info


stac = STACTiler(router_prefix="stac")
```

### Custom PathParams for `path_dependency`

One common customization could be to create your own `path_dependency` (used in all endpoints).

Here an example which allow a mosaic to be passed by a layer name instead of a full S3 url.

```python
import os
import re
from titiler.dependencies import DefaultDependency
from typing import Optional, Type
from rio_tiler.io import BaseReader
from fastapi import HTTPException, Query

MOSAIC_BACKEND = os.getenv("TITILER_MOSAIC_BACKEND")
MOSAIC_HOST = os.getenv("TITILER_MOSAIC_HOST")


@dataclass
class PathParams(DefaultDependency):
    """Create dataset path from args"""

    mosaic: str = Query(..., description="mosaic name")

    # We need url and reader to match default PathParams signature
    # Because we set `init=False` those params won't appear in OpenAPI docs.
    url: Optional[str] = field(init=False, default=None)
    reader: Optional[Type[BaseReader]] = field(init=False, default=None)  # Placeholder

    def __post_init__(self,):
        """Define dataset URL."""
        # mosaic name should be in form of `{user}.{layername}`
        if not re.match(self.mosaic, r"^[a-zA-Z0-9-_]{1,32}\.[a-zA-Z0-9-_]{1,32}$"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mosaic name {self.mosaic}.",
            )

        self.url = f"{MOSAIC_BACKEND}{MOSAIC_HOST}/{self.mosaic}.json.gz"
```

### Custom TMS

```python

import morecantile
from rasterio.crs import CRS

from titiler.endpoint.factory import TMSTilerFactory

# 1. Create Custom TMS
EPSG6933 = morecantile.TileMatrixSet.custom(
    (-17357881.81713629, -7324184.56362408, 17357881.81713629, 7324184.56362408),
    CRS.from_epsg(6933),
    identifier="EPSG6933",
    matrix_scale=[1, 1],
)

# 2. Register TMS
morecantile.tms.register(custom_tms.EPSG6933)

# 3. Create ENUM with available TMS
TileMatrixSetNames = Enum(  # type: ignore
    "TileMatrixSetNames", [(a, a) for a in sorted(morecantile.tms.list())]
)

# 4. Create Custom TMS dependency
def TMSParams(
    TileMatrixSetId: TileMatrixSetNames = Query(
        TileMatrixSetNames.WebMercatorQuad,  # type: ignore
        description="TileMatrixSet Name (default: 'WebMercatorQuad')",
    )
) -> morecantile.TileMatrixSet:
    """TileMatrixSet Dependency."""
    return morecantile.tms.get(TileMatrixSetId.name)

# 5. Create Tiler
COGTilerWithCustomTMS = TMSTilerFactory(
    reader=COGReader,
    tms_dependency=TMSParams,
)
```
