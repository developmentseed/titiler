# Tiler Factories

Tiler factories are helper functions that let you create a customized FastAPI router.

```python
from titiler.endpoints.factory import TilerFactory

tiler = TilerFactory()

print([r.path for r in tiler.router.routes])
> [
    '/bounds',
    '/info',
    '/metadata',
    '/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}',
    '/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x',
    '/tiles/{TileMatrixSetId}/{z}/{x}/{y}.{format}',
    '/tiles/{TileMatrixSetId}/{z}/{x}/{y}',
    '/tiles/{z}/{x}/{y}@{scale}x.{format}',
    '/tiles/{z}/{x}/{y}@{scale}x',
    '/tiles/{z}/{x}/{y}.{format}',
    '/tiles/{z}/{x}/{y}',
    '/{TileMatrixSetId}/tilejson.json',
    '/tilejson.json',
    '/{TileMatrixSetId}/WMTSCapabilities.xml',
    '/WMTSCapabilities.xml',
    '/point/{lon},{lat}',
    '/preview.{format}',
    '/preview',
]
```

## Factories

Router created with the Tiler Factories will have basic routes:

* `/bounds`
* `/info`
* `/tiles/...`
* `/tilesjon.json`
* `/WMTSCapabilities.xml`
* `/point`

### TilerFactory

placeholder

### TMSTilerFactory

placeholder

### MosaicTilerFactory

placeholder

## Readers

placeholder

## Dependencies

If you are new the concept of **Dependency Injection**, please checkout this awesome tutorial: https://fastapi.tiangolo.com/tutorial/dependencies/

In titiler `Factories`, we use the dependencies to define the inputs for each endpoints (and thus the OpenAPI documention).

Example:
```python
@dataclass
class ImageParams:
    """Common Image parameters."""

    max_size: Optional[int] = Query(
        1024, description="Maximum image size to read onto."
    )
    height: Optional[int] = Query(None, description="Force output image height.")
    width: Optional[int] = Query(None, description="Force output image width.")

    def __post_init__(self):
        """Post Init."""
        super().__post_init__()

        if self.width and self.height:
            self.max_size = None


@router.get(r"/preview.png")
def preview(
    url: str = Query(..., description="data set URL"), params: ImageParams = Depends(),
):

    with COGReader(url) as cog:
        data, mask = cog.preview(
            max_size=params.max_size,
            width=params.width,
            height=params.height,
        )
```

The `factories` allow users to set multiple default dependencies. Here is the list of common dependencies and their default values:

* **path_dependency**: Set dataset path (url).
    ```python
    @dataclass
    class PathParams(DefaultDependency):
        """Create dataset path from args"""

        url: str = Query(..., description="Dataset URL")

        # Placeholder
        # Factory can accept a reader defined in the PathParams.
        # This is for case where a user would want to indicate in the input url what
        # reader to use:
        # landsat+{landsat scene id}
        # sentinel+{sentinel scene id}
        # ...
        reader: Optional[Type[BaseReader]] = field(init=False, default=None)
    ```

* **tiles_dependency**
    ```python
    @dataclass
    class CommonParams(DefaultDependency):
        """Common Reader params."""

        bidx: Optional[str] = Query(
            None, title="Band indexes", description="comma (',') delimited band indexes",
        )
        nodata: Optional[Union[str, int, float]] = Query(
            None, title="Nodata value", description="Overwrite internal Nodata value"
        )
        resampling_method: ResamplingNames = Query(
            ResamplingNames.nearest, description="Resampling method."  # type: ignore
        )

        def __post_init__(self):
            """Post Init."""
            self.indexes = (
                tuple(int(s) for s in re.findall(r"\d+", self.bidx)) if self.bidx else None
            )
            if self.nodata is not None:
                self.nodata = numpy.nan if self.nodata == "nan" else float(self.nodata)

    @dataclass
    class TileParams(CommonParams):
        """Common Tile parameters."""

        expression: Optional[str] = Query(
            None,
            title="Band Math expression",
            description="rio-tiler's band math expression (e.g B1/B2)",
        )
        rescale: Optional[str] = Query(
            None,
            title="Min/Max data Rescaling",
            description="comma (',') delimited Min,Max bounds",
        )
        color_formula: Optional[str] = Query(
            None,
            title="Color Formula",
            description="rio-color formula (info: https://github.com/mapbox/rio-color)",
        )
        color_map: Optional[ColorMapNames] = Query(
            None, description="rio-tiler's colormap name"
        )
        colormap: Optional[Dict[int, Tuple[int, int, int, int]]] = field(init=False)

        def __post_init__(self):
            """Post Init."""
            super().__post_init__()

            self.colormap = cmap.get(self.color_map.value) if self.color_map else None
    ```


* **point_dependency**: Set band indexes or expression and allow overriding of the nodata value.
    ```python
    @dataclass
    class PointParams(DefaultDependency):
        """Point Parameters."""

        bidx: Optional[str] = Query(
            None, title="Band indexes", description="comma (',') delimited band indexes",
        )
        nodata: Optional[Union[str, int, float]] = Query(
            None, title="Nodata value", description="Overwrite internal Nodata value"
        )
        expression: Optional[str] = Query(
            None,
            title="Band Math expression",
            description="rio-tiler's band math expression (e.g B1/B2)",
        )

        def __post_init__(self):
            """Post Init."""
            self.indexes = (
                tuple(int(s) for s in re.findall(r"\d+", self.bidx)) if self.bidx else None
            )
            if self.nodata is not None:
                self.nodata = numpy.nan if self.nodata == "nan" else float(self.nodata)
    ```

* **tms_dependency**: The TMS dependency set the available TMS for a tile endpoint.
    ```python
    # Allow all morecantile TMS
    def TMSParams(
        TileMatrixSetId: TileMatrixSetNames = Query(
            TileMatrixSetNames.WebMercatorQuad,  # type: ignore
            description="TileMatrixSet Name (default: 'WebMercatorQuad')",
        )
    ) -> morecantile.TileMatrixSet:
        """TileMatrixSet Dependency."""
        return morecantile.tms.get(TileMatrixSetId.name)
    
    # or
    # Restrict the TMS to `WebMercatorQuad` only
    def WebMercatorTMSParams(
        TileMatrixSetId: WebMercatorTileMatrixSetName = Query(
            WebMercatorTileMatrixSetName.WebMercatorQuad,  # type: ignore
            description="TileMatrixSet Name (default: 'WebMercatorQuad')",
        )
    ) -> morecantile.TileMatrixSet:
        """TileMatrixSet Dependency."""
        return morecantile.tms.get(TileMatrixSetId.name)
    ```

* **additional_dependency**: Default dependency, will be passed are `**options.kwargs` to all reader methods.

    ```python
    @dataclass
    class DefaultDependency:
        """Dependency Base Class"""

        kwargs: dict = field(init=False, default_factory=dict)
    ```

For `TMSTilerFactory` and `TilerFactory`
* **metadata_dependency**: `rio_tiler.io.BaseReader.metadata()` methods options
```python
@dataclass
class MetadataParams(CommonParams):
    """Common Metadada parameters."""

    pmin: float = Query(2.0, description="Minimum percentile")
    pmax: float = Query(98.0, description="Maximum percentile")
    max_size: int = Query(1024, description="Maximum image size to read onto.")
    histogram_bins: Optional[int] = Query(None, description="Histogram bins.")
    histogram_range: Optional[str] = Query(
        None, description="comma (',') delimited Min,Max histogram bounds"
    )
    bounds: Optional[str] = Query(
        None,
        descriptions="comma (',') delimited Bounding box coordinates from which to calculate image statistics.",
    )
    hist_options: dict = field(init=False, default_factory=dict)

    def __post_init__(self):
        """Post Init."""
        super().__post_init__()

        if self.histogram_bins:
            self.hist_options.update(dict(bins=self.histogram_bins))
        if self.histogram_range:
            self.hist_options.update(
                dict(range=list(map(float, self.histogram_range.split(","))))
            )
        if self.bounds:
            self.bounds = tuple(map(float, self.bounds.split(",")))
```

* **img_dependency**: 
```python
@dataclass
class ImageParams(TileParams):
    """Common Image parameters."""

    max_size: Optional[int] = Query(
        1024, description="Maximum image size to read onto."
    )
    height: Optional[int] = Query(None, description="Force output image height.")
    width: Optional[int] = Query(None, description="Force output image width.")

    def __post_init__(self):
        """Post Init."""
        super().__post_init__()

        if self.width and self.height:
            self.max_size = None
```

## Customization

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
