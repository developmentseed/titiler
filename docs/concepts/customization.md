
### Example of STAC Tiler

While a STAC tiler is included in the default TiTiler application, it provides
an illustrative example of why one might need a custom tiler. The default
factories create endpoints that expect basic input like `indexes=[1, 2, 3]` and
`resampling_method='nearest'` but STAC needs more info. The STAC reader provided
by `rio-tiler` and `rio-tiler-crs` needs an `assets=` option to specify which
STAC asset(s) you want to read.

We can add additional dependencies to endpoint by using the `additional_dependency` options when creating the factory.

```python
from dataclasses import dataclass
from titiler.endpoints.factory import TilerFactory
from rio_tiler_crs import STACReader
from titiler.dependencies import DefaultDependency

@dataclass
class AssetsParams(DefaultDependency):
    """Asset and Band indexes parameters."""

    assets: Optional[str] = Query(
        None,
        title="Asset indexes",
        description="comma (',') delimited asset names (might not be an available options of some readers)",
    )

    def __post_init__(self):
        """Post Init."""
        if self.assets is not None:
            self.kwargs["assets"] = self.assets.split(",")


stac = TilerFactory(
    reader=STACReader,
    additional_dependency=AssetsParams,
    router_prefix="stac",
)
```

With `additional_dependency` set to `AssetsParams`, each endpoint will now have `assets` as one of input function.

While this is good, it's not enough. STACTiler `metadata()` and `info()` methods return a slightly different output that the usual COGReader (because of multiple assets). We then need to customize a bit more the tiler:

```python
from titiler.dependencies import DefaultDependency
from titiler.endpoint.factory import TilerFactory
from titiler.models.cog import cogInfo, cogMetadata


@dataclass
class AssetsBidxParams(DefaultDependency):
    """Asset and Band indexes parameters."""

    assets: Optional[str] = Query(
        None,
        title="Asset indexes",
        description="comma (',') delimited asset names (might not be an available options of some readers)",
    )
    bidx: Optional[str] = Query(
        None, title="Band indexes", description="comma (',') delimited band indexes",
    )

    def __post_init__(self):
        """Post Init."""
        if self.assets is not None:
            self.kwargs["assets"] = self.assets.split(",")
        if self.bidx is not None:
            self.kwargs["indexes"] = tuple(
                int(s) for s in re.findall(r"\d+", self.bidx)
            )


@dataclass
class AssetsBidxExprParams(DefaultDependency):
    """Assets, Band Indexes and Expression parameters."""

    assets: Optional[str] = Query(
        None,
        title="Asset indexes",
        description="comma (',') delimited asset names (might not be an available options of some readers)",
    )
    expression: Optional[str] = Query(
        None,
        title="Band Math expression",
        description="rio-tiler's band math expression (e.g B1/B2)",
    )
    bidx: Optional[str] = Query(
        None, title="Band indexes", description="comma (',') delimited band indexes",
    )

    def __post_init__(self):
        """Post Init."""
        if self.assets is not None:
            self.kwargs["assets"] = self.assets.split(",")
        if self.expression is not None:
            self.kwargs["expression"] = self.expression
        if self.bidx is not None:
            self.kwargs["indexes"] = tuple(
                int(s) for s in re.findall(r"\d+", self.bidx)
            )


# We create a Sub-Class from the TilerFactory and update 2 methods.
@dataclass
class STACTiler(TilerFactory):
    """Custom Tiler Class for STAC."""

    reader: Type[STACReader] = STACReader  # We set the Reader to STACReader by default

    layer_dependency: Type[DefaultDependency] = AssetsBidxExprParams

    # Overwrite info method to return the list of assets when no assets is passed.
    # 2 changes from the _info in the original factory:
    # - response_model:
    #    response_model=cogInfo -> response_model=Union[List[str], Dict[str, cogInfo]]
    #    The output of STACTiler.info is a dict in form of {"asset1": {`cogIngo`}}
    # - Return list of assets if no `assets` option passed
    #    This can be usefull in case we don't know the assets present in the STAC item.
    def info(self):
        """Register /info endpoint."""

        @self.router.get(
            "/info",
            response_model=Union[List[str], Dict[str, Info]],
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={200: {"description": "Return dataset's basic info."}},
        )
        def info(
            src_path=Depends(self.path_dependency),
            asset_params=Depends(AssetsBidxParams),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Return basic info."""
            with self.reader(src_path.url, **self.reader_options) as src_dst:
                # `Assets` is a required options for `info`,
                # if not set we return the list of assets
                if not asset_params.assets:
                    return src_dst.assets
                info = src_dst.info(**asset_params.kwargs, **kwargs)
            return info


    # Overwrite _metadata method because the STACTiler output model is different
    # response_model=cogMetadata -> response_model=Dict[str, cogMetadata]
    # Same as for info(), we update the output model to match the output result from STACTiler.metadata
    def metadata(self):
        """Register /metadata endpoint."""

        @self.router.get(
            "/metadata",
            response_model=Dict[str, Metadata],
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={200: {"description": "Return dataset's metadata."}},
        )
        def metadata(
            src_path=Depends(self.path_dependency),
            asset_params=Depends(AssetsBidxParams),
            metadata_params=Depends(self.metadata_dependency),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Return metadata."""
            with self.reader(src_path.url, **self.reader_options) as src_dst:
                info = src_dst.metadata(
                    metadata_params.pmin,
                    metadata_params.pmax,
                    **asset_params.kwargs,
                    **metadata_params.kwargs,
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

    # We need url to match default PathParams signature
    # Because we set `init=False` those params won't appear in OpenAPI docs.
    url: Optional[str] = field(init=False, default=None)

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

from morecantile import tms, TileMatrixSet
from rasterio.crs import CRS

from titiler.endpoint.factory import TilerFactory

# 1. Create Custom TMS
EPSG6933 = TileMatrixSet.custom(
    (-17357881.81713629, -7324184.56362408, 17357881.81713629, 7324184.56362408),
    CRS.from_epsg(6933),
    identifier="EPSG6933",
    matrix_scale=[1, 1],
)

# 2. Register TMS
tms = tms.register([EPSG6933])

# 3. Create ENUM with available TMS
TileMatrixSetNames = Enum(  # type: ignore
    "TileMatrixSetNames", [(a, a) for a in sorted(tms.list())]
)

# 4. Create Custom TMS dependency
def TMSParams(
    TileMatrixSetId: TileMatrixSetNames = Query(
        TileMatrixSetNames.WebMercatorQuad,  # type: ignore
        description="TileMatrixSet Name (default: 'WebMercatorQuad')",
    )
) -> TileMatrixSet:
    """TileMatrixSet Dependency."""
    return tms.get(TileMatrixSetId.name)

# 5. Create Tiler
COGTilerWithCustomTMS = TilerFactory(
    reader=COGReader,
    tms_dependency=TMSParams,
)
```
