# Release Notes

## Unreleased

* Remove all default values to the dependencies
    * `DatasetParams.unscale`: `False` -> `None` (default to `False` in rio-tiler)
    * `DatasetParams.resampling_method`: `nearest` -> `None` (default to `nearest` in rio-tiler)
    * `DatasetParams.reproject_method`: `nearest` -> `None` (default to `nearest` in rio-tiler)
    * `ImageRenderingParams.add_mask`: `True` -> `None` (default to `True` in rio-tiler)
    * `StatisticsParams.categorical`: `False` -> `None` (default to `False` in rio-tiler)

* Add `as_dict(exclude_none=True/False)` method to the `DefaultDependency` class.

    ```python
    from typing import Optional
    from titiler.core.dependencies import DefaultDependency
    from dataclasses import dataclass

    @dataclass
    class Deps(DefaultDependency):
        value: Optional[int] = None

    print({**Deps().__dict__.items()})
    >> {'value': None}

    Deps().as_dict()  # `exclude_none` defaults to True
    >> {}

    Deps(value=1).as_dict()
    >> {'value': 1}
    ```

* Use `.as_dict()` method when passing option to rio-tiler Reader's methods to avoid parameter conflicts when using custom Readers.

## 0.18.5 (2024-07-03)

* Set version requirement for FastAPI to `>=0.111.0`

## 0.18.4 (2024-06-26)

* fix Tiles URL encoding for WMTSCapabilities XML document

## 0.18.3 (2024-05-20)

* fix `WMTSCapabilities.xml` response for ArcMap compatibility
    * replace `Cloud Optimized GeoTIFF` with dataset URL or `TiTiler` for the *ows:ServiceIdentification* **title**
    * replace `cogeo` with `Dataset` for the `layer` *ows:Identifier*

## 0.18.2 (2024-05-07)

* move to `fastapi-slim` to avoid unwanted dependencies (author @n8sty, https://github.com/developmentseed/titiler/pull/815)

## 0.18.1 (2024-04-12)

### titiler.core

* fix `TerrainRGB` algorithm name (author @JinIgarashi, https://github.com/developmentseed/titiler/pull/804)
* add more tests for `RescalingParams` and `HistogramParams` dependencies
* make sure to return *empty* content for `204` Error code

## 0.18.0 (2024-03-22)

### titiler.core

* Add `ColorMapFactory` to create colorMap metadata endpoints (https://github.com/developmentseed/titiler/pull/796)
* **Deprecation** remove default `WebMercatorQuad` tile matrix set in `/tiles`, `/tilesjson.json`, `/map` and `/WMTSCapabilities.xml` endpoints (https://github.com/developmentseed/titiler/pull/802)

    ```
    # Before
    /tiles/{z}/{x}/{y}
    /tilejson.json
    /map
    /WMTSCapabilities.xml

    # Now
    /tiles/WebMercatorQuad/{z}/{x}/{y}
    /WebMercatorQuad/tilejson.json
    /WebMercatorQuad/map
    /WebMercatorQuad/WMTSCapabilities.xml
    ```

* **Deprecation** `default_tms` attribute in `BaseTilerFactory` (because `tileMatrixSetId` is now required in endpoints).

### titiler.mosaic

* **Deprecation** remove default `WebMercatorQuad` tile matrix set in `/tiles`, `/tilesjson.json`, `/map` and `/WMTSCapabilities.xml` endpoints (https://github.com/developmentseed/titiler/pull/802)

    ```
    # Before
    /tiles/{z}/{x}/{y}
    /tilejson.json
    /map
    /WMTSCapabilities.xml

    # Now
    /tiles/WebMercatorQuad/{z}/{x}/{y}
    /WebMercatorQuad/tilejson.json
    /WebMercatorQuad/map
    /WebMercatorQuad/WMTSCapabilities.xml
    ```

* **Deprecation** `default_tms` attribute in `MosaicTilerFactory` (because `tileMatrixSetId` is now required in endpoints).

### Misc

* add `request` as first argument in `TemplateResponse` to adapt with latest starlette version

## 0.17.3 (2024-03-21)

### titiler.application

* Add `extra="ignore"` option `ApiSettings` to fix pydantic issue when using `.env` file (author @imanshafiei540, https://github.com/developmentseed/titiler/pull/800)

## 0.17.2 (2024-03-15)

### titiler.core

* fix OpenAPI metadata for algorithm (author @JinIgarashi, https://github.com/developmentseed/titiler/pull/797)

## 0.17.1 (2024-03-13)

* add python 3.12 support

### titiler.core

* Add `use_epsg` parameter to WMTS endpoint to resolve ArcMAP issues and fix XML formating (author @gadomski, https://github.com/developmentseed/titiler/pull/782)
* Add more OpenAPI metadata for algorithm (author @JinIgarashi, https://github.com/developmentseed/titiler/pull/783)

### titiler.application

* fix invalid url parsing in HTML responses

## 0.17.0 (2024-01-17)

### titiler.core

* update `rio-tiler` version to `>6.3.0`
* use new `align_bounds_with_dataset=True` rio-tiler option in GeoJSON statistics methods for more precise calculation

## 0.16.2 (2024-01-17)

### titiler.core

* fix leafletjs template maxZoom to great than 18 for `/map` endpoint (author @Firefishy, https://github.com/developmentseed/titiler/pull/749)

## 0.16.1 (2024-01-08)

### titiler.core

* use morecantile `TileMatrixSet.cellSize` property instead of deprecated/private `TileMatrixSet._resolution` method

### titiler.mosaic

* use morecantile `TileMatrixSet.cellSize` property instead of deprecated/private `TileMatrixSet._resolution` method

## 0.16.0 (2024-01-08)

### titiler.core

* update FastAPI version lower limit to `>=0.107.0`
* fix template loading for starlette >= 0.28 by using `jinja2.Environment` argument (author @jasongi, https://github.com/developmentseed/titiler/pull/744)

### titiler.extensions

* fix template loading for starlette >= 0.28 by using `jinja2.Environment` argument (author @jasongi, https://github.com/developmentseed/titiler/pull/744)

### titiler.application

* fix template loading for starlette >= 0.28 by using `jinja2.Environment` argument (author @jasongi, https://github.com/developmentseed/titiler/pull/744)

## 0.15.8 (2024-01-08)

### titiler.core

* use morecantile `TileMatrixSet.cellSize` property instead of deprecated/private `TileMatrixSet._resolution` method [backported from 0.16.1]

### titiler.mosaic

* use morecantile `TileMatrixSet.cellSize` property instead of deprecated/private `TileMatrixSet._resolution` method [backported from 0.16.1]

## 0.15.7 (2024-01-08)

### titiler.core

* update FastAPI version upper limit to `<0.107.0` to avoid starlette breaking change (`0.28`)

### titiler.application

* add simple *auth* (optional) based on `global_access_token` string, set with `TITILER_API_GLOBAL_ACCESS_TOKEN` environment variable (author @DeflateAwning, https://github.com/developmentseed/titiler/pull/735)

## 0.15.6 (2023-11-16)

### titiler.core

* in `/map` HTML response, add Lat/Lon buffer to AOI to avoid creating wrong AOI (when data covers the whole world).

## 0.15.5 (2023-11-09)

### titiler.core

* add `algorithm` options for `/statistics` endpoints

* switch from `BaseReader.statistics()` method to a combination of `BaseReader.preview()` and `ImageData.statistics()` methods to get the statistics

## 0.15.4 (2023-11-06)

### titiler.core

* update `rio-tiler` requirement to `>=6.2.5,<7.0`

* allow `bidx` option in `titiler.core.dependencies.AssetsBidxExprParams` and `titiler.core.dependencies.AssetsBidxParams`

    ```python
    # merge band 1 form asset1 and asset2
    # before
    httpx.get(
        "/stac/preview",
        params=(
            ("url", "stac.json"),
            ("assets", "asset1"),
            ("assets", "asset2"),
            ("asset_bidx", "asset1|1"),
            ("asset_bidx", "asset2|1"),
        )
    )

    # now
    httpx.get(
        "/stac/preview",
        params=(
            ("url", "stac.json"),
            ("assets", "asset1"),
            ("assets", "asset2"),
            ("bidx", 1),
        )
    )
    ```

* fix openapi examples

## 0.15.3 (2023-11-02)

* add `dst_crs` options in `/statistics [POST]` and `/feature [POST]` endpoints

## 0.15.2 (2023-10-23)

### titiler.core

* add `dependencies.TileParams` dependency with `buffer` and `padding` options
* add `tile_dependency` attribute in `TilerFactory` class (defaults to `TileParams`)
* add `reproject` (alias to `reproject_method`) option in `DatasetParams` dependency

### titiler.mosaic

*  Change `HTTP_404_NOT_FOUND` to `HTTP_204_NO_CONTENT` when no asset is found or tile is empty (author @simouel, https://github.com/developmentseed/titiler/pull/713)
* add `tile_dependency` attribute in `MosaicTilerFactory` class (defaults to `TileParams`)

### cdk application

* Support non-root paths in AWS API Gateway Lambda handler (author @DanSchoppe, https://github.com/developmentseed/titiler/pull/716)

## 0.15.1 (2023-10-17)

* Allow a default `color_formula` parameter to be set via a dependency (author @samn, https://github.com/developmentseed/titiler/pull/707)
* add `titiler.core.dependencies.create_colormap_dependency` to create ColorMapParams dependency from `rio_tiler.colormap.ColorMaps` object
* add `py.typed` files in titiler submodules (https://peps.python.org/pep-0561)

## 0.15.0 (2023-09-28)

### titiler.core

- added `PartFeatureParams` dependency

**breaking changes**

- `max_size` is now set to `None` for `/statistics [POST]`, `/bbox` and `/feature` endpoints, meaning the tiler will create image from the highest resolution.

- renamed `titiler.core.dependencies.ImageParams` to `PreviewParams`

- split TileFactory `img_dependency` attribute in two:
  - `img_preview_dependency`: used in `/preview` and `/statistics [GET]`, default to `PreviewParams` (with `max_size=1024`)

  - `img_part_dependency`: used in `/bbox`, `/feature` and `/statistics [POST]`, default to `PartFeatureParams` (with `max_size=None`)

- renamed `/crop` endpoints to `/bbox/...` or `/feature/...`
  - `/crop/{minx},{miny},{maxx},{maxy}.{format}` -> `/bbox/{minx},{miny},{maxx},{maxy}.{format}`

  - `/crop/{minx},{miny},{maxx},{maxy}/{width}x{height}.{format}` -> `/bbox/{minx},{miny},{maxx},{maxy}/{width}x{height}.{format}`

  - `/crop [POST]` -> `/feature [POST]`

  - `/crop.{format} [POST]` -> `/feature.{format} [POST]`

  - `/crop/{width}x{height}.{format}  [POST]` -> `/feature/{width}x{height}.{format} [POST]`

- update `rio-tiler` requirement to `>=6.2.1`

- Take coverage weights in account when generating statistics from GeoJSON features

## 0.14.1 (2023-09-14)

### titiler.extension

* add `GetFeatureInfo` capability in `wmsExtension` (author @benjaminleighton, https://github.com/developmentseed/titiler/pull/698)

## 0.14.0 (2023-08-30)

### titiler.core

* replace `-` by `_` in query parameters **breaking change**
  - `coord-crs` -> `coord_crs`
  - `dst-crs` -> `dst_crs`

* replace `buffer` and `color_formula` endpoint parameters by external dependencies (`BufferParams` and `ColorFormulaParams`)

* add `titiler.core.utils.render_image` which allow non-binary alpha band created with custom colormap. `render_image` replace `ImageData.render` method.

    ```python
    # before
    if cmap := colormap or dst_colormap:
        image = image.apply_colormap(cmap)

    if not format:
        format = ImageType.jpeg if image.mask.all() else ImageType.png

    content = image.render(
        img_format=format.driver,
        **format.profile,
        **render_params,
    )

    # now
    # render_image will:
    # - apply the colormap
    # - choose the right output format if `None`
    # - create the binary data
    content, media_type = render_image(
        image,
        output_format=format,
        colormap=colormap or dst_colormap,
        **render_params,
    )
    ```

### titiler.extension

* rename `geom-densify-pts` to `geometry_densify` **breaking change**
* rename `geom-precision` to `geometry_precision` **breaking change**

## 0.13.3 (2023-08-27)

* fix Factories `url_for` method and avoid changing `Request.path_params` object

## 0.13.2 (2023-08-24)

### titiler.extensions

* replace mapbox-gl by maplibre
* replace Stamen by OpenStreetMap tiles
* simplify band selection handling (author @tayden, https://github.com/developmentseed/titiler/pull/688)

## 0.13.1 (2023-08-21)

### titiler.core

* fix `LowerCaseQueryStringMiddleware` unexpectedly truncating query parameters (authors @jthetzel and @jackharrhy, @https://github.com/developmentseed/titiler/pull/677)

## titiler.application

* add `cors_allow_methods` in `ApiSettings` to control the CORS allowed methods (author @ubi15, https://github.com/developmentseed/titiler/pull/684)

## 0.13.0 (2023-07-27)

* update core requirements to libraries using pydantic **~=2.0**

### titiler.core

* update requirements:
  * fastapi `>=0.95.1` --> `>=0.100.0`
  * pydantic `~=1.0` --> `~=2.0`
  * rio-tiler `>=5.0,<6.0` --> `>=6.0,<7.0`
  * morecantile`>=4.3,<5.0` --> `>=5.0,<6.0`
  * geojson-pydantic `>=0.4,<0.7` --> `>=1.0,<2.0`
  * typing_extensions `>=4.6.1`

### titiler.extension

* update requirements:
  * rio-cogeo `>=4.0,<5.0"` --> `>=5.0,<6.0"`

### titiler.mosaic

* update requirements:
  * cogeo-mosaic `>=6.0,<7.0` --> `>=7.0,<8.0`

### titiler.application

* use `/api` and `/api.html` for documentation (instead of `/openapi.json` and `/docs`)
* update landing page

## 0.12.0 (2023-07-17)

* use `Annotated` Type for Query/Path parameters
* replace variable `TileMatrixSetId` by `tileMatrixSetId`

### titiler.core

* update FastAPI dependency to `>=0.95.1`
* set `pydantic` dependency to `~=1.0`
* update `rio-tiler` dependency to `>=5.0,<6.0`
* update TMS endpoints to match OGC Tiles specification

### titiler.extensions

* use TiTiler's custom JSONResponse for the `/validate` endpoint to avoid issue when COG has `NaN` nodata value
* update `rio-cogeo` dependency to `>=4.0,<5.0`
* update `rio-stac` requirement to `>=0.8,<0.9` and add `geom-densify-pts` and `geom-precision` options

## titiler.mosaic

* update `cogeo-mosaic` dependency to `>=6.0,<7.0`
* remove `titiler.mosaic.resources.enum.PixelSelectionMethod` and use `rio_tiler.mosaic.methods.PixelSelectionMethod`
* allow more TileMatrixSet (than only `WebMercatorQuad`)

## 0.11.7 (2023-05-18)

### titiler.core

* make HTML `templates` configurable in the factories
* rename `index.html` to `map.html`
* rename `dependencies.CRSParams` to `dependencies.CoordCRSParams`
* add `dst-crs` option for `/preview` and `/crop` endpoints to specify the output Coordinate Reference System.

### titiler.mosaic

* make HTML `templates` configurable in the factories

### titiler.extensions

* make HTML `templates` configurable in the factories
* rename `cog_index.html` to `cog_viewer.html`
* rename `stac_index.html` to `stac_viewer.html`
* add `zoom to point` in `stac` and `cog` viewers (author @dchirst, https://github.com/developmentseed/titiler/pull/614)

## 0.11.6 (2023-04-14)

* Allow a default `rescale` parameter to be set via a dependency (author @samn, https://github.com/developmentseed/titiler/pull/619)
* add `coord-crs` parameter for `/point`, `/part` and `/feature` endpoints

## 0.11.5 (2023-03-22)

* fix `TerrainRGB` (change interval from `1.0` to `0.1`)

## 0.11.4 (2023-03-20)

* set FastAPI version lower than 0.95 (https://github.com/tiangolo/fastapi/discussions/9278)

## 0.11.3 (2023-03-14)

* handle dateline crossing dataset in COG/STAC Viewer
* update Factories `url_for` method to make sure we return a string (https://github.com/developmentseed/titiler/pull/607)

## 0.11.2 (2023-03-08)

* Add OSM background in `/map` viewer when using WebMercator TMS

## 0.11.1 (2023-03-01)

* no change since 0.11.1a0

## 0.11.1a0 (2023-03-01)

* switch to `hatch` and `pdm-pep517` as build system and use `pyproject.toml` for python module metadata
* switch to `ruff` for python linting
* update pre-commit configuration
* documentation fixes 🙏 (authors @jthetzel, @neilsh)
* fix documentation about `asset_bidx`

### titiler.core

* Algorithm change, make terrainrgb interval and baseval floats to support more quantizers (author @AndrewAnnex, https://github.com/developmentseed/titiler/pull/587)
* update `rio-tiler` minimum version to `4.1.6`
* Apply colormap before defining image output format (when not provided)

### titiler.mosaic

* Apply colormap before defining image output format (when not provided)

## 0.11.0 (2023-01-27)

* add `titiler.extensions` package (`cogValidateExtension`, `stacExtension`, `cogViewerExtension`,  `stacViewerExtension`, `wmsExtension`)

### titiler.mosaic

* update `cogeo-mosaic` version requirement to `>=5.0,<5.2` (allow using `az://` prefix from uri)
* add `MOSAIC_STRICT_ZOOM` environment variable to control if the application should allow fetching tiles outside mosaic min/max zooms

**breaking change**

### titiler.core

* add `extensions` option to the `BaseTilerFactory` to specify a list of extension we want to register. Each extension will be then registered in the `__post_init__` object creation step.
* remove `BaseHTTPMiddleware` class inheritance for middleware (write pure ASGI middleware)

### titiler.application

* uses Extension to add more endpoints to default `titiler.core` factories
* move all `viewer` code into `titiler.extensions`
* add `/cog/stac` endpoint from `titiler.extension.stacExtension` to create STAC Items from raster dataset

### titiler.mosaic

* removed deprecated *empty* path (`/` is the correct route path, which enable prefixed and non-prefixed mosaic application)

## 0.10.2 (2022-12-17)

* fix issue with new morecantile version
* replace path parameter in `router_prefix` in `BaseTilerFactory.url_for`

## 0.10.1 (2022-12-15)

* update `/map` endpoint and template to support multiple TMS (https://github.com/developmentseed/titiler/pull/560)

## 0.10.0 (2022-12-09)

**breaking change**

* Simplify dependency requirements for titiler.mosaic and titiler.application and using `=={currentVersion}`

### titiler.core

* fix the `wmts.xml` template to work with non-epsg based CRS

### titiler.application

* fix titiler.application viewer when using dataset with band name in metadata

## 0.9.0 (2022-12-05)

### titiler.core

* add `default_tms` in `BaseTilerFactory` to set the default TMS identifier supported by the tiler (e.g `WebMercatorQuad`)

## 0.8.1 (2022-12-01)

### titiler.core

* remove useless `titiler.core.version` file

## 0.8.0 (2022-12-01)

* remove python 3.7 support
* add python 3.10 and 3.11 in CI

### titiler.core

* update FastAPI requirement to `>=0.87`
* update rio-tiler requirement to `>=4.1,<4.2`
* remove `rescale` and `color_formula` from the `post_process` dependency
* add `algorithm` support and introduce new `algorithm` and `algorithm_params` query parameters

**breaking changes**

* remove `timing headers` and `titiler.core.utils` submodule
* remove `asset_expression` (except in `/asset_statistics` endpoint) (see https://cogeotiff.github.io/rio-tiler/v4_migration/#multibasereader-expressions)
* update Point output model to include `band_names`
* histogram and info band names are prefixed with `b` (e.g `b1`) (ref: https://cogeotiff.github.io/rio-tiler/v4_migration/#band-names)
* add `/map` endpoint in TilerFactory to display tiles given query-parameters
* remove `TMSParams` and `WebMercatorTMSParams` dependencies.
* replace `TilerFactory.tms_dependency` attribute by `TilerFactory.supported_tms`. This attribute gets a `morecantile.defaults.TileMatrixSets` store and will create the tms dependencies dynamically
* replace `TMSFactory.tms_dependency` attribute by `TMSFactory.supported_tms`. This attribute gets a `morecantile.defaults.TileMatrixSets` store and will create the tms dependencies dynamically
* move `stats_dependency` and `histogram_dependency` from `BaseTilerFactory` to `TilerFactory`
* per rio-tiler changes, `;` has be to used in expression to indicate multiple bands. `b1*2,b2+b3,b1/b3` -> `b1*2;b2+b3;b1/b3`

### titiler.mosaic

* update cogeo-mosaic requirement to `>=4.2,<4.3`

**breaking changes**

* remove `timing headers`
* replace `MosaicTilerFactory.tms_dependency` attribute by `MosaicTilerFactory.supported_tms`. This attribute gets a `morecantile.defaults.TileMatrixSets` store and will create the tms dependencies dynamically

### titiler.application

* code simplification by removing custom code and submodules from endpoints

**breaking changes**

* remove custom TMS and custom Colormap dependencies
* remove middleware submodule


## 0.7.1 (2022-09-21)

### titiler.mosaic

* add `pixel_selection_dependency` options in `MosaicTilerFactory` to allow default method override (author @samn, https://github.com/developmentseed/titiler/pull/495)

### titiler.application

* allow `interval` colormaps in titiler.application

### Helm charts

* Check Charts workflow added for the Helm charts testing (author @emmanuelmathot, https://github.com/developmentseed/titiler/pull/495)

## 0.7.0 (2022-06-08)

* add `environment_dependency` option in `BaseTilerFactory` to define GDAL environment at runtime.
* remove `gdal_config` option in `BaseTilerFactory` **breaking**

```python
# before
router = TilerFactory(gdal_config={"GDAL_DISABLE_READDIR_ON_OPEN": "FALSE"}).router

# now
router = TilerFactory(environment_dependency=lambda: {"GDAL_DISABLE_READDIR_ON_OPEN": "FALSE"}).router


class ReaddirType(str, Enum):

    false = "false"
    true = "true"
    empty_dir = "empty_dir"


# or at endpoint call. The user could choose between false/true/empty_dir
def gdal_env(disable_read: ReaddirType = Query(ReaddirType.false)):
    return {"GDAL_DISABLE_READDIR_ON_OPEN": disable_read.value.upper()}

router = TilerFactory(environment_dependency=gdal_env).router
```

### titiler.application

* update `starlette-cramjam` requirement

## 0.6.0 (2022-05-13)

* no change since `0.6.0a2`

## 0.6.0a2 (2022-05-11)

* revert to `setup.py` + `setuptools` instead of `pyproject.toml` + `flit` because it broke namespace packages (https://github.com/developmentseed/titiler/pull/472)

## 0.6.0a1 (2022-05-11)

### titiler.core

* remove logging in error `exception_handler_factory`
* add optional `reader_dependency` to enable passing `Reader`'s option defined by Query/Header/Path parameters.
* switch to `pyproject.toml`
* move version definition in `titiler.core.__version__` **breaking**
* Include all values for a query param in `LowerCaseQueryStringMiddleware` (author @samn, https://github.com/developmentseed/titiler/pull/464)

### titiler.mosaic

* add optional `backend_dependency` to enable passing `Backend`'s option defined by Query/Header/Path parameters.
* remove `backend_options` MosaicTilerFactory argument in favor of the use of `backend_dependency` **breaking**
* switch to `pyproject.toml`
* move version definition in `titiler.mosaic.__version__` **breaking**

### titiler.application

* Fix frontend to handle anti-meridian crossing data
* switch to `pyproject.toml`
* move version definition in `titiler.application.__version__` **breaking**

## 0.5.1 (2022-03-07)

* add `cachecontrol_max_http_code` option to `CacheControlMiddleware` to avoid adding cache-control headers for API errors (Author @sharkinsspatial, https://github.com/developmentseed/titiler/pull/444)

## 0.5.0 (2022-02-22)

* update rio-tiler/morecantile/rio-cogeo/cogeo-mosaic versions
* add MultiBaseTilerFactory `/asset_statistics` which will return *per asset* statistics. Returns response in form of `Dict[{asset name}, Dict[{band name}, BandStatistics]]`

**breaking change**

* Multi-band expression now uses semicolon `;` instead of colon (`,`) as separator. Note: proper urlencoding might be needed.

```python
# before
expression = "b1+b2,b2"

# new
expression = "b1+b2;b2"
```

* MultiBaseTilerFactory `/statistics` now returns *merged* statistics in form of `Dict[{asset_band or expression}, BandStatistics]` (instead of `Dict[{asset name}, Dict[{band name}, BandStatistics]]`)

```python
# before
response = httpx.get(f"/stac/statistics?url=item.json").json()
print(response)
>>> {
    "asset1": {
        "1": {
            "min": ...,
            "max": ...,
            ...
        },
        "2": {
            "min": ...,
            "max": ...,
            ...
        }
    }
}

# now
response = httpx.get(f"/stac/statistics?url=item.json").json()
print(response)
>>> {
    "asset1_1": {
        "min": ...,
        "max": ...,
        ...
    },
    "asset1_2": {
        "min": ...,
        "max": ...,
        ...
    },
}
```

## 0.4.3 (2022-02-08)

* add tile `buffer` option to match rio-tiler tile options (https://github.com/developmentseed/titiler/pull/427)

## 0.4.2 (2022-01-25)

### titiler.core

* update minimum FastAPI version to `>=0.73` (https://github.com/developmentseed/titiler/pull/425)

## 0.4.1 (2022-01-25)

### titiler.core

* update type information for the factory `colormap_dependency`

### k8s
* Update ingress k8s templates to be compatible with latest resource types versions (https://github.com/developmentseed/titiler/pull/425

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
