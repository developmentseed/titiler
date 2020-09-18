# Release Notes

## Next (TBD) - Master

* exclude `tests/` an `stack/` in titiler python package.
* add `EPSG6933` in TMS
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

    def metadata(
        src_path=Depends(self.path_dependency),
        metadata_params=Depends(self.metadata_dependency),
        kwargs=Depends(self.additional_dependency),
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

**breaking changes**
-  [FACTORY] the `additional_dependency` should be a Callable which return a dict.

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
