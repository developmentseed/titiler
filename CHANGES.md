# Release Notes

## 0.4.0 (2021-11-30)

* rename `Dockerfile` to `Dockerfile.gunicorn`
* switch default docker image to python3.9
* add `Dockerfile.uvicorn`

### titiler.core

* update `rio-tiler` version requirement to `>=3.0`

### titiler.mosaic

* update `cogeo-mosaic` version to `>=4.0`

## 0.4.0a2 (2021-11-24)

### titiler.core

* update `rio-tiler` version (>=3.0.0a6) with new colormap types information and base classes
* remove `additional_dependency` attribute in `BaseTileFactory`. This also remove `**kwargs` in endpoints **breaking**
* remove `reader_options` attribute in `BaseTileFactory` **breaking**
* `tms_dependency` default to `titiler.core.dependencies.TMSParams` which should supports all morecantile's TMS.
* add `route_dependencies` attribute to `BaseTilerFactory` to allow customizing route dependencies (author @alukach, https://github.com/developmentseed/titiler/pull/406)

### titiler.mosaic

* update `cogeo-mosaic` version (>=4.0.0a2) with updated Backend type hints information

## 0.4.0a1 (2021-11-12)

* fix titiler packages cross dependencies

## 0.4.0a0 (2021-11-12)

* remove python 3.6 supports (related to morecantile/pyproj update)

### titiler.core

* update `rio-tiler/morecantile` requirement (>=3.0)
* remove `utils.bbox_to_feature` (replaced by geojson_pydantic native function `Feature(geometry=Polygon.from_bounds(*bounds), properties=info)`)
* remove `utils.data_stats` (replaced by rio-tiler new statistics method)
* remove `metadata` endpoints  **breaking API**
* update `statistics` endpoints with histogram options
* update `statistics` endpoint responses **breaking API**
* remove `band_expression` in `BandsExprParams` dependency **breaking API**
* remove `morecantile` requirement definition in setup.py and defers to rio-tiler supported version
* update `titiler.core.dependencies.DefaultDependency` (allows dict unpacking and remove `.kwargs`) **breaking API**
* use standard for List in QueryParameter (e.g `bidx=1&bidx=2&bidx` instead of `bidx=1,2,3`) **breaking API**
* add `asset_bidx` query parameter in replacement of `bidx` in MultiBaseFactory dependencies and switch to new format: `{asset name}|{bidx,bidx,bidx}` **breaking API**
* update `asset_expression` to the new format: `{asset name}|{expression}` (e.g `data|b1+b2`) **breaking API**
* update `assets` QueryParameter to List (e.g `assets=COG&assets=Data`) **breaking API**
* update `bands` QueryParameter to List (e.g `bands=B01&bands=B02`) **breaking API**
* split `RenderParams` dependency into:
    * `PostProcessParams`: `rescale` and `color_formula` parameters
    * `ImageRenderingParams`: `return_mask`
* add `process_dependency` attribute in `BaseTilerFactory` (defaults to `PostProcessParams`)
* use `resampling` alias instead of `resampling_method` for QueryParameter **breaking API**
* defaults to available assets if `assets` option is not provided for `MultiBaseTilerFactory` info and statistics endpoints.
* defaults to available bands if `bands` option is not provided for `MultiBandsTilerFactory` info and statistics endpoints.
* better output models definition
* keep `bounds`, `minzoom` and `maxzoom` in `/info` response
* remove `dataset` in `/info` response to better follow the Info model
* add `/statistics` endpoint by default

### titiler.mosaic

* update `cogeo-mosaic` requirement (>=4.0)
* update response from `/info` endpoint to match the model.

### titiler.application

* update viewers to match changes in titiler.core endpoints

## 0.3.12 (2021-10-20)

### titiler.core

- Update morecantile requirement to stay under `3.0` (author @robintw, https://github.com/developmentseed/titiler/pull/389)

## 0.3.11 (2021-10-07)

### titiler.application

- Update rio-cogeo requirement to stay under `3.0`

## 0.3.10 (2021-09-23)

### titiler.core

- add custom JSONResponse using [simplejson](https://simplejson.readthedocs.io/en/latest/) to allow NaN/inf/-inf values (ref: https://github.com/developmentseed/titiler/pull/374)
- use `titiler.core.resources.responses.JSONResponse` as default response for `info`, `metadata`, `statistics` and `point` endpoints (ref: https://github.com/developmentseed/titiler/pull/374)

### titiler.application

- switch to `starlette_cramjam` compression middleware (ref: https://github.com/developmentseed/titiler/issues/369)

## 0.3.9 (2021-09-07)

### titiler.core

- update FastAPI requirements to `>=0.65,<0.68` (ref: https://github.com/developmentseed/titiler/issues/366)
- surface `asset_expression` and `band_expression` in Multi*TilerFactory (ref: https://github.com/developmentseed/titiler/issues/367)

## 0.3.8 (2021-09-02)

### titiler.core

- move `titiler.application.middleware` to `titiler.core.middleware` (https://github.com/developmentseed/titiler/pull/365)

## 0.3.7 (2021-09-01)

### titiler.core

- Update the TileJSON model for better validation and to match with the specification (center is optional) (https://github.com/developmentseed/titiler/pull/363)

## 0.3.6 (2021-08-23)

### titiler.core

- fix morecantile related tests (https://github.com/developmentseed/titiler/issues/358)
- fix float parsing when datatype is float32 (https://github.com/developmentseed/rio-viz/issues/39)

### titiler.application

- fix morecantile related tests (https://github.com/developmentseed/titiler/issues/358)

## 0.3.5 (2021-08-17)

### titiler.mosaic

* add `/{z}/{x}/{y}/assets`, `/{lon},{lat}/assets`, `/{minx},{miny},{maxx},{maxy}/assets` GET endpoints to return a list of assets that intersect a given geometry (author @mackdelany, https://github.com/developmentseed/titiler/pull/351)

## 0.3.4 (2021-08-02) - **Not published on PyPi** [#355](https://github.com/developmentseed/titiler/discussions/355)

### titiler.core

* add `/crop` POST endpoint to return an image from a GeoJSON feature (https://github.com/developmentseed/titiler/pull/339)
* add `/statistics` (GET and POST) endpoints to return advanced images statistics (https://github.com/developmentseed/titiler/pull/347)

### titiler.application

* add optional `root_path` setting to specify a url path prefix to use when running the app behind a reverse proxy (https://github.com/developmentseed/titiler/pull/343)

## 0.3.3 (2021-06-29) - **Not published on PyPi** [#355](https://github.com/developmentseed/titiler/discussions/355)

### titiler.core

* fix possible bug when querystring parameter are case insensitive (https://github.com/developmentseed/titiler/pull/323)

### titiler.mosaic

* update `tilejson` and `WMTSCapabilities.xml` endpoints to allow list querystrings (as done previously in https://github.com/developmentseed/titiler/issues/319)

### titiler.application

* add `titiler.application.middleware.LowerCaseQueryStringMiddleware` to cast all query string parameter to lowercase (author @lorenzori, https://github.com/developmentseed/titiler/pull/321)

### code and repo

* move `titiler` code to `src/titiler`

## 0.3.2 (2021-05-26)

### titiler.core

* update rio-tiler dependency to `>=2.1` version and update `rescale` query-parameter (https://github.com/developmentseed/titiler/issues/319)

```
# before
# previously, rio-tiler was splitting a list of input range in tuple of 2
rescale=0,1000,0,1000,0,1000

# now
# rio-tiler 2.1 now expect sequence of tuple in form of Sequence[Tuple[Num, Num]]
rescale=0,1000&rescale=0,1000&rescale=0,1000
```

### titiler.mosaic

* update `cogeo-mosaic` version to `>=3.0,<3.1`.

### titiler.application

* re-order middlewares (https://github.com/developmentseed/titiler/issues/311)
* update rio-cogeo version to `>=2.2` and use `rio_cogeo.models` instead of custom ones.


## 0.3.1 (2021-04-27)

* add `exclude_path` options in `titiler.application.middleware.CacheControlMiddleware` to avoid adding cache-control headers to specific paths.
* allow `histogram_bins` to be a single value or a `,` delimited scalar (https://github.com/developmentseed/titiler/pull/307)
* change error status from `404` to `500` for `RasterioIOError` exception (author @kylebarron, https://github.com/developmentseed/titiler/pull/300)

    Sometimes GDAL/Rasterio can lose track of the file handler (might be related to cache issue + threading) and raise `RasterioIOError: file not found`, while the file exists for real. To avoid caching this, we changed the error code to 500 (errors >= 500 do not get `cache-control` header on titiler.application).

## 0.3.0 (2021-04-19)

* add support for `.jpg` and `.jpeg` extensions (https://github.com/developmentseed/titiler/pull/271)
* better error message when parsing the colormap value fails (https://github.com/developmentseed/titiler/pull/279)

**breaking change**

* split `titiler` into a set of namespaces packages (https://github.com/developmentseed/titiler/pull/284)

    **titiler.core**

    The `core` package host the low level tiler factories.
    ```python
    # before
    from titiler.endpoints.factory import TilerFactory

    # now
    from titiler.core.factory import TilerFactory
    ```

    **titiler.mosaic**

    The `mosaic` package is a plugin to `titiler.core` which adds support for MosaicJSON
    ```python
    # before
    from titiler.endpoints.factory import MosaicTilerFactory

    # now
    from titiler.mosaic.factory import MosaicTilerFactory
    ```

    **titiler.application**

    The `application` package is a full `ready to use` FastAPI application with support of STAC, COG and MosaicJSON.

    ```bash
    # before
    $ pip install titiler
    $ uvicorn titiler.main:app --reload

    # now
    $ pip install titiler.application uvicorn
    $ uvicorn titiler.application.main:app --reload
    ```

## 0.2.0 (2021-03-09)

* adapt for cogeo-mosaic `3.0.0rc2` and add `backend_options` attribute in MosaicTilerFactory (https://github.com/developmentseed/titiler/pull/247)
* update FastAPI requirements
* update minimal python version to 3.6
* add `**render_params.kwargs` to pass custom render params in `image.render` method (https://github.com/developmentseed/titiler/pull/259)
* Changed probe url from `/ping` to `/healthz` in k8s deployment

**breaking change**

* renamed `OptionalHeaders`, `MimeTypes` and `ImageDrivers` enums to the singular form (https://github.com/developmentseed/titiler/pull/258)
* renamed titiler.dependencies's Enums (`ColorMapName`, `ResamplingName` and `TileMatrixSetName`) to the singular form (https://github.com/developmentseed/titiler/pull/260)
* renamed `MimeType` to `MediaType` (https://github.com/developmentseed/titiler/pull/258)
* add `ColorMapParams` dependency to ease the creation of custom colormap dependency (https://github.com/developmentseed/titiler/pull/252)
* renamed `PathParams` to `DatasetPathParams` and also made it a simple callable (https://github.com/developmentseed/titiler/pull/260)
* renamed `colormap` query-parameter to `colormap_name` (https://github.com/developmentseed/titiler/pull/262)
    ```
    # before
    /cog/preview.png?colormap=viridis

    # now
    /cog/preview.png?colormap_name=viridis
    ```

* use `colormap` query-parameter to pass custom colormap (https://github.com/developmentseed/titiler/pull/262)
    ```
    /cog/preview.png?colormap={"0": "#FFFF00FF", ...}
    ```

## 0.1.0 (2021-02-17)

* update FastAPI requirements
* add `validate` in `MosaicTilerFactory` (https://github.com/developmentseed/titiler/pull/206, author @drnextgis)
* rename `ressources` package to `resources` (https://github.com/developmentseed/titiler/pull/210, author @drnextgis)
* renamed environment variables prefixes for API and STACK configurations: `TITILER_STACK` as prefix to CDK and `TITILER_API` as prefix to API (https://github.com/developmentseed/titiler/pull/211, author @fredliporace)
* remove MosaicTilerFactory `create` and `update` endpoints (https://github.com/developmentseed/titiler/pull/218)
* deleted `titiler.models.mosaics` because the models are not used anymore (https://github.com/developmentseed/titiler/pull/221)
* update rio-tiler and cogeo-mosaic minimal versions (https://github.com/developmentseed/titiler/pull/220, https://github.com/developmentseed/titiler/pull/213)
* move STAC related dependencies to `titiler.dependencies (https://github.com/developmentseed/titiler/pull/225)
* add `rio_tiler.io.MultiBandReader` bands dependencies (https://github.com/developmentseed/titiler/pull/226)
* add `MultiBaseTilerFactory` and `MultiBandTilerFactory` custom tiler factories (https://github.com/developmentseed/titiler/pull/230)
* Update STAC tiler to use the new `MultiBaseTilerFactory` factory
* depreciate *empty* GET endpoint for MosaicTilerFactory read (https://github.com/developmentseed/titiler/pull/232)
* better `debug` configuration and make reponse headers metadata optional (https://github.com/developmentseed/titiler/pull/232)

**breaking change**

* update `titiler.dependencies.AssetsBidxParams` to make `asset` a required parameter (https://github.com/developmentseed/titiler/pull/230
* the STAC `/info` endpoint now expect the `assets` parameter to be passed. To ge the list of available assets we added a new `/assets` endpoint within the tiler factory
* remove `COGReader` as default `reader` in `titiler.endpoints.factory.BaseTilerFactory`

## 0.1.0a14 (2021-01-05)

* add `rio_tiler.errors.MissingBands` in known errors.
* add `titiler.endpoints.factory.TMSFactory` to enable custom TMS endpoints.
* **breaking** rename `BaseFactory` to `BaseTilerFactory` in `titiler.endpoints.factory`

## 0.1.0a13 (2020-12-20)

* allow `API_DISABLE_{COG/STAC/MOSAIC}` environment variables to control default endpoints in titiler main app (https://github.com/developmentseed/titiler/issues/156)
* add `overwriting=False/True` on MosaicJSON creation (https://github.com/developmentseed/titiler/issues/164)
* add `gdal_config` option to Tiler factories to replace custom `APIRoute` class (https://github.com/developmentseed/titiler/issues/168)
* add `info.geojson` endpoint to return dataset info as a GeoJSON feature (https://github.com/developmentseed/titiler/issues/166)
* update `rio-tiler`, `cogeo-mosaic` and optional dependencies

## 0.1.0a12 (2020-11-18)

* require `rio-tiler>=2.0.0rc2`
* update Enums for Image types. (**breaking**)
* Add more output datatype (jpeg2000, pngraw)
* add `width/height` in `/crop` endpoint path

```
/crop/{minx},{miny},{maxx},{maxy}.{format}
/crop/{minx},{miny},{maxx},{maxy}/{width}x{height}.{format}
```

## 0.1.0a11.post1 (2020-11-12)

* relax version for rio-tiler and cogeo-mosaic

```python
"rio-cogeo~=2.0"
"rio-tiler>=2.0.0rc1,<2.1"
"cogeo-mosaic>=3.0.0a17,<3.1"
```

## 0.1.0a11 (2020-11-12)

* split `tile()` for `MosaicTilerFactory` method (https://github.com/developmentseed/titiler/issues/147)

## 0.1.0a10 (2020-11-09)

* update for rio-tiler==2.0.0rc1, cogeo-mosaic==3.0.0a17 and morecantile==2.0
* split `tile()` factory method (https://github.com/developmentseed/titiler/issues/141, author @fredliporace)

## 0.1.0a9 (2020-10-26)

* avoid changing mutable TMS and Colormap list by using deepcopy.
* quiet/turn off logs
* add logger middleware (https://github.com/developmentseed/titiler/pull/139)

## 0.1.0a8 (2020-10-13)

* update for rio-tiler 2.0.0b17, which now support TMS (morecantile) by default.
* update fastapi minimum version to 0.61

**breaking changes**

* removed TMSTilerFactory (because default reader built with rio_tiler BaseReader should support TMS).

Note: We changed the versioning scheme to `{major}.{minor}.{path}{pre}{prenum}`

## 0.1.0-alpha.7 (2020-10-13)

* remove `pkg_resources` (https://github.com/pypa/setuptools/issues/510)

## 0.1.0-alpha.6 (2020-10-05)

* refactor CacheControl Middleware
* rename headers value `X-Server-Timings` to `Server-Timing`.
* add `total;dur={}` in response header `Server-Timing`, using new `titiler.middleware.TotalTimeMiddleware` middleware (113)

```python
from titiler.middleware import CacheControlMiddleware, TotalTimeMiddleware
from fastapi import FastAPI

app.add_middleware(CacheControlMiddleware, cachecontrol="public, max-age=3600")
app.add_middleware(TotalTimeMiddleware)
```

* Add Brotli compression support (#126, author @kylebarron)
* Numerous fix to CDK app.py (co-author @kylebarron)

## 0.1.0-alpha.5 (2020-09-22)

* exclude `tests/` an `stack/` in titiler python package.
* add `EPSG6933` in TMS

**breaking changes**
* [FACTORY] the `additional_dependency` should be a Callable which return a dict.

    ```python
    @dataclass  # type: ignore
    class BaseFactory(metaclass=abc.ABCMeta):
        """BaseTiler Factory."""
        ...
        # provide custom dependency
        additional_dependency: Callable[..., Dict] = field(default=lambda: dict())
    ```

    ```python
    def AssetsParams(
        assets: Optional[str] = Query(
            None,
            title="Asset indexes",
            description="comma (',') delimited asset names (might not be an available options of some readers)",
        )
    ) -> Dict:
        """Assets Dependency."""
        kwargs = {}
        if assets:
            kwargs["assets"] = assets.split(",")
        return kwargs
    ```
* [FACTORY] remove `_` prefix in factory methods (e.g `_tile` -> `tile`)
* [FACTORY] refactor dependencies to better align with rio_tiler.io.BaseReader method definition.

    Example:

    In the `metadata`, the `MetadataParams` will be used to pass `pmin` and `pmax` because they are the only
    required parameters for the metadata method. All other params will be passed to a `kwargs` dict.

    ```python
    @dataclass
    class MetadataParams(DefaultDependency):
        """Common Metadada parameters."""
        # Required params
        pmin: float = Query(2.0, description="Minimum percentile")
        pmax: float = Query(98.0, description="Maximum percentile")
        # Optional parameters
        bidx: Optional[str] = Query(
            None, title="Band indexes", description="comma (',') delimited band indexes",
        )
        ...
        def __post_init__(self):
            """Post Init."""

            if self.bidx is not None:
                self.kwargs["indexes"] = tuple(
                    int(s) for s in re.findall(r"\d+", self.bidx)
                )
        ...

    # metadata method in factory
    def metadata(
        src_path=Depends(self.path_dependency),
        metadata_params=Depends(self.metadata_dependency),
        kwargs: Dict = Depends(self.additional_dependency),
    ):
        """Return metadata."""
        reader = src_path.reader or self.reader
        with reader(src_path.url, **self.reader_options) as src_dst:
            info = src_dst.metadata(
                metadata_params.pmin,
                metadata_params.pmax,
                **metadata_params.kwargs,
                **kwargs,
            )
        return info
    ```
* [FACTORY] refactor dependencies definition
    ```python
    @dataclass  # type: ignore
    class BaseFactory(metaclass=abc.ABCMeta):
        """BaseTiler Factory."""

        reader: default_readers_type = field(default=COGReader)
        reader_options: Dict = field(default_factory=dict)

        # FastAPI router
        router: APIRouter = field(default_factory=APIRouter)

        # Path Dependency
        path_dependency: Type[PathParams] = field(default=PathParams)

        # Rasterio Dataset Options (nodata, unscale, resampling)
        dataset_dependency: default_deps_type = field(default=DatasetParams)

        # Indexes/Expression Dependencies
        layer_dependency: default_deps_type = field(default=BidxExprParams)

        # Image rendering Dependencies
        render_dependency: default_deps_type = field(default=RenderParams)

        # TileMatrixSet dependency
        tms_dependency: Callable[..., TileMatrixSet] = WebMercatorTMSParams

        # provide custom dependency
        additional_dependency: Callable[..., Dict] = field(default=lambda: dict())
    ```

* remove `PathParams.reader` attribute. This option was not used and would have been technically difficult to use.
    ```python
    @dataclass
    class PathParams:
        """Create dataset path from args"""

        url: str = Query(..., description="Dataset URL")
    ```


## 0.1.0-alpha.4 (2020-09-14)

* Update `.npy` output format to follow the numpyTile format (#103)

    ```python
    import numpy
    import requests
    from io import BytesIO

    endpoint = ...
    url = "https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif"

    r = requests.get(f"{endpoint}/cog/tiles/14/10818/9146.npy",
        params = {
            "url": url,
        }
    )
    data = numpy.load(BytesIO(r.content))
    print(data.shape)
    > (4, 256, 256)
    ```

* Add `titiler.custom.routing.apiroute_factory`. This function enable the creation of custom fastapi.routing.APIRoute class with `rasterio.Env()` block.

    ```python
    from fastapi import FastAPI, APIRouter
    from rasterio._env import get_gdal_config
    from titiler.custom.routing import apiroute_factory

    app = FastAPI()
    route_class = apiroute_factory({"GDAL_DISABLE_READDIR_ON_OPEN": "FALSE"})
    router = APIRouter(route_class=route_class)

    @router.get("/simple")
    def simple():
        """should return FALSE."""
        res = get_gdal_config("GDAL_DISABLE_READDIR_ON_OPEN")
        return {"env": res}

    app.include_router(router)
    ```

    Note: This has only be tested for python 3.6 and 3.7.


## 0.1.0-alpha.3 (2020-09-03)

* add custom `url_for` method in TilerFactory to retrieve `prefixed` endpoint URL (#95)
* remove magic `titiler.dependencies.PathParams` mosaicid path translation, where a user could pass `url=mosaicid://` to the endpoint.
* switch to `pydantic.BaseSettings` for FastAPI application setting management.

    List of Settings:

    ```python
    name: str = "titiler"
    cors_origins: str = "*"
    cachecontrol: str = "public, max-age=3600"
    ```

API Settings can now be set by adding a `.env` file in your local project or by setting environment variables (e.g `API_CORS_ORIGIN="https://mywebsite.com/*"`)

## 0.1.0-alpha.2 (2020-09-01)

* add Transform and CRS information in `/part` GeoTIFF output
* pin **rio-tiler-crs** to `>=3.0b4,<3.1` and **cogeo-mosaic** to `>=3.0a10,<3.1`

## 0.1.0-alpha.1 (2020-09-01)

* rename titiler.models.cog.py to titiler.models.dataset.py
* remove cog* prefix to Bounds, Info and Metadata models
* allow Union[str, int] for key in Metadata.statistics (as defined in rio-tiler-pds)

e.g Create a Landsat 8 Tiler
```python
from titiler.endpoints.factory import TilerFactory, MosaicTilerFactory
from titiler.dependencies import BandsParams

from rio_tiler_pds.landsat.aws.landsat8 import L8Reader  # Not in TiTiler dependencies

from fastapi import FastAPI

app = FastAPI(title="Landsat Tiler", openapi_url="/api/v1/openapi.json")
scene = TilerFactory(
    reader=L8Reader, additional_dependency=BandsParams, router_prefix="scenes"
)
mosaic = MosaicTilerFactory(
    dataset_reader=L8Reader,
    additional_dependency=BandsParams,
    add_update=False,
    add_create=False,
    router_prefix="mosaic",
)
app.include_router(scene.router, prefix="/scenes", tags=["Scenes"])
app.include_router(mosaic.router, prefix="/mosaic", tags=["Mosaic"])
```

## 0.1a0 (2020-08-31)

**First release on pypi**

### Tiler Factory

For this release we created new Tiler Factories class which handle creation of FastAPI routers for a given rio_tiler **Readers**.

```python
from titiler.endpoints.factory import TilerFactory
from rio_tiler.io import COGReader, STACReader

from fastapi import FastAPI

app = FastAPI()

cog = TilerFactory()
app.include_router(cog.router, tags=["Cloud Optimized GeoTIFF"])
```

#### Readers / TileMatrixSets

The `titiler.endpoints.factory.TilerFactory` class will create a tiler with `Web Mercator` as uniq supported Tile Matrix Set.

For other TMS support, tiler needs to be created with `titiler.endpoints.factory.TMSTilerFactory` and with a TMS friendly reader (e.g `rio_tiler_crs.COGReader`).

**Simple tiler with only Web Mercator support**
```python
from rio_tiler.io import COGReader

from titiler.endpoints import factory
from titiler.dependencies import WebMercatorTMSParams

app = factory.TilerFactory(reader=COGReader)
assert app.tms_dependency == WebMercatorTMSParams
```

**Tiler with more TMS support (from morecantile)**
```python
from rio_tiler_crs import COGReader

from titiler.endpoints import factory
from titiler.dependencies import TMSParams

app = factory.TMSTilerFactory(reader=COGReader)
assert app.tms_dependency == TMSParams
```

### Other changes

* add mosaic support  (#17 author @geospatial-jeff)
* update to rio-tiler-crs>=3.0b* and rio-tiler>=2.0b*
* Pin fastapi version to 0.60.1
* Remove titiler.core in favor of starlette settings (#55, author @geospatial-jeff)
* Add fastapi exception handlers (#56, author @geospatial-jeff)
* Remove intermediary routers (#57, author @geospatial-jeff)
* Remove /titiler/api submodule (e.g titiler.api.utils -> titiler.utils)
* Add Cache-Control middleware. Endpoints do not define any cache-control headers. (part of #43, co-author with @geospatial-jeff)
* Add 'X-Assets' in response headers for mosaic tiles (#51)
* add cog validation via rio-cogeo (co-author with @geospatial-jeff, #37)

### Breaking changes

* default tiler to Web Mercator only
* removed cache layer for tiles
* updated html templates

```python
template_dir = pkg_resources.resource_filename("titiler", "templates")
templates = Jinja2Templates(directory=template_dir)

cog_template = templates.TemplateResponse(
    name="cog_index.html",
    context={
        "request": request,
        "tilejson": request.url_for("cog_tilejson"),
        "metadata": request.url_for("cog_metadata"),
    },
    media_type="text/html",
)

stac_template = templates.TemplateResponse(
    name="stac_index.html",
    context={
        "request": request,
        "tilejson": request.url_for("stac_tilejson"),
        "metadata": request.url_for("stac_info"),
    },
    media_type="text/html",
)
```

## Pre Pypi releases

## 2.1.2 (2020-06-24)

* add `width` & `height` parameters in API docs to force output size for part/preview endpoints.
* add `resampling_method` in API docs.

link: https://github.com/developmentseed/titiler/commit/725da5fa1bc56d8e192ae8ff0ad107493ca93378

## 2.1.1 (2020-06-22)

* add minimum fastapi version (0.54.0) and update docker config

link: https://github.com/developmentseed/titiler/commit/95b98a32ffb3274d546dd52f99a3920091029b4c

## 2.1.0 (2020-06-11)

* add `/preview`, `/crop`, `/point` endpoints

link: https://github.com/developmentseed/titiler/commit/8b63fc6b6141b9c9361c95d80897d77b5e2d47c3

## 2.0.0 (2020-06-09)

* support STAC items (#16)
* better API documentation via response models
* update UI (`/stac/viewer`, `/cog/viewer`)
* re-order OpenAPI route tags
* update documentation

link: https://github.com/developmentseed/titiler/commit/fa2cb78906b0fd88506b89bace8174969be8cd4f

## 1.0.0 (2020-06-04)

Initial release

link: https://github.com/developmentseed/titiler/commit/f4fdc02ea0235470589eeb34a4da8e5aae74e696
