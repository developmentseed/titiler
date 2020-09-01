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

## Readers

placeholder

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


### Custom Tiler: STAC Tiler

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
