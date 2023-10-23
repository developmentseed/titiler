
Tiler factories are helper functions that let users create a FastAPI router (`fastapi.APIRouter`) with a minimal set of endpoints.

### BaseTilerFactory

All **Factories** are built from an [abstract based class](https://docs.python.org/3/library/abc.html) which is used to define commons attributes and utility functions shared between all factories.

#### Methods

- **register_routes**: Abstract method which needs to be define by each factories.
- **url_for**: Method to construct endpoint URL
- **add_route_dependencies**: Add dependencies to routes.

#### Attributes

- **reader**: Dataset Reader **required**.
- **router**: FastAPI router. Defaults to `fastapi.APIRouter`.
- **path_dependency**: Dependency to use to define the dataset url. Defaults to `titiler.core.dependencies.DatasetPathParams`.
- **layer_dependency**: Dependency to define band indexes or expression. Defaults to `titiler.core.dependencies.BidxExprParams`.
- **dataset_dependency**: Dependency to overwrite `nodata` value, apply `rescaling` and change the `I/O` or `Warp` resamplings. Defaults to `titiler.core.dependencies.DatasetParams`.
- **process_dependency**: Dependency to control which `algorithm` to apply to the data. Defaults to `titiler.core.algorithm.algorithms.dependency`.
- **rescale_dependency**: Dependency to set Min/Max values to rescale from, to 0 -> 255. Defaults to `titiler.core.dependencies.RescalingParams`.
- **color_formula_dependency**: Dependency to define the Color Formula. Defaults to `titiler.core.dependencies.ColorFormulaParams`.
- **colormap_dependency**: Dependency to define the Colormap options. Defaults to `titiler.core.dependencies.ColorMapParams`
- **render_dependency**: Dependency to control output image rendering options. Defaults to `titiler.core.dependencies.ImageRenderingParams`
- **environment_dependency**: Dependency to defile GDAL environment at runtime. Default to `lambda: {}`.

- **supported_tms**:
- **default_tms**: Set default `TileMatrixSet` identifier to use. Defaults to `WebMercatorQuad`.
- **router_prefix**: Set prefix to all factory's endpoint. Defaults to `""`.
- **optional_headers**: List of `OptionalHeader` which endpoints could add (if implemented). Defaults to `[]`.
- **route_dependencies**: Additional routes dependencies to add after routes creations. Defaults to `[]`.
- **extension**: TiTiler extensions to register after endpoints creations. Defaults to `[]`.
- **templates**: *Jinja2* templates to use in endpoints. Defaults to `titiler.core.factory.DEFAULT_TEMPLATES`


## TilerFactory

Factory meant to create endpoints for single dataset using [*rio-tiler*'s `Reader`](https://cogeotiff.github.io/rio-tiler/readers/#rio_tileriorasterioreader).

#### Attributes

- **reader**: Dataset Reader. Defaults to `Reader`.
- **stats_dependency**: Dependency to define options for *rio-tiler*'s statistics method used in `/statistics` endpoints. Defaults to `titiler.core.dependencies.StatisticsParams`.
- **histogram_dependency**: Dependency to define *numpy*'s histogram options used in `/statistics` endpoints. Defaults to `titiler.core.dependencies.HistogramParams`.
- **img_preview_dependency**: Dependency to define image size for `/preview` and `/statistics` endpoints. Defaults to `titiler.core.dependencies.PreviewParams`.
- **img_part_dependency**: Dependency to define image size for `/bbox` and `/feature` endpoints. Defaults to `titiler.core.dependencies.PartFeatureParams`.
- **tile_dependency**: Dependency to defile `buffer` and `padding` to apply at tile creation. Defaults to `titiler.core.dependencies.TileParams`.
- **add_preview**: . Defaults to `True`
- **add_part**: . Defaults to `True`
- **add_viewer**: . Defaults to `True`

#### Endpoints

```python
from fastapi import FastAPI

from titiler.core.factory import TilerFactory

app = FastAPI()
cog = TilerFactory()
app.include_router(cog.router
```

| Method | URL                                                             | Output                                      | Description
| ------ | --------------------------------------------------------------- |-------------------------------------------- |--------------
| `GET`  | `/bounds`                                                       | JSON ([Bounds][bounds_model])               | return dataset's bounds
| `GET`  | `/info`                                                         | JSON ([Info][info_model])                   | return dataset's basic info
| `GET`  | `/info.geojson`                                                 | GeoJSON ([InfoGeoJSON][info_geojson_model]) | return dataset's basic info as a GeoJSON feature
| `GET`  | `/statistics`                                                   | JSON ([Statistics][stats_model])            | return dataset's statistics
| `POST` | `/statistics`                                                   | GeoJSON ([Statistics][stats_geojson_model]) | return dataset's statistics for a GeoJSON
| `GET`  | `/tiles[/{tileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`  | image/bin                                   | create a web map tile image from a dataset
| `GET`  | `[/{tileMatrixSetId}]/tilejson.json`                            | JSON ([TileJSON][tilejson_model])           | return a Mapbox TileJSON document
| `GET`  | `[/{tileMatrixSetId}]/WMTSCapabilities.xml`                     | XML                                         | return OGC WMTS Get Capabilities
| `GET`  | `/point/{lon},{lat}`                                            | JSON ([Point][point_model])                 | return pixel values from a dataset
| `GET`  | `/preview[.{format}]`                                           | image/bin                                   | create a preview image from a dataset (**Optional**)
| `GET`  | `/bbox/{minx},{miny},{maxx},{maxy}[/{width}x{height}].{format}` | image/bin                                   | create an image from part of a dataset (**Optional**)
| `POST` | `/feature[/{width}x{height}][.{format}]`                           | image/bin                                   | create an image from a GeoJSON feature (**Optional**)
| `GET`  | `/map`                                                          | HTML                                        | return a simple map viewer
| `GET`  | `[/{tileMatrixSetId}]/map`                                      | HTML                                        | return a simple map viewer


## MultiBaseTilerFactory

Custom `TilerFactory` to be used with [`rio_tiler.io.MultiBaseReader`](http://127.0.0.1:8000/titiler/advanced/tiler_factories/#titilercorefactorymultibasetilerfactory) type readers (e.g `rio_tiler.io.STACReader`).

#### Attributes

- **layer_dependency**: Dependency to define assets or expression. Defaults to `titiler.core.dependencies.AssetsBidxExprParams`.
- **assets_dependency**: Dependency to define assets to be used. Defaults to `titiler.core.dependencies.AssetsParams`.

#### Endpoints

```python
from fastapi import FastAPI
# rio_tiler.io.STACReader is a MultiBaseReader
from rio_tiler.io import STACReader

from titiler.core.factory import MultiBaseTilerFactory

app = FastAPI()
stac = MultiBaseTilerFactory(reader=STACReader)
app.include_router(stac.router])
```

| Method | URL                                                             | Output                                           | Description
| ------ | --------------------------------------------------------------- |------------------------------------------------- |--------------
| `GET`  | `/bounds`                                                       | JSON ([Bounds][bounds_model])                    | return dataset's bounds
| `GET`  | `/assets`                                                       | JSON                                             | return the list of available assets
| `GET`  | `/info`                                                         | JSON ([Info][multiinfo_model])                   | return assets basic info
| `GET`  | `/info.geojson`                                                 | GeoJSON ([InfoGeoJSON][multiinfo_geojson_model]) | return assets basic info as a GeoJSON feature
| `GET`  | `/asset_statistics`                                             | JSON ([Statistics][multistats_model])            | return per asset statistics
| `GET`  | `/statistics`                                                   | JSON ([Statistics][stats_model])                 | return assets statistics (merged)
| `POST` | `/statistics`                                                   | GeoJSON ([Statistics][multistats_geojson_model]) | return assets statistics for a GeoJSON (merged)
| `GET`  | `/tiles[/{tileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`  | image/bin                                        | create a web map tile image from assets
| `GET`  | `/[{tileMatrixSetId}]/tilejson.json`                            | JSON ([TileJSON][tilejson_model])                | return a Mapbox TileJSON document
| `GET`  | `/{tileMatrixSetId}/WMTSCapabilities.xml`                       | XML                                              | return OGC WMTS Get Capabilities
| `GET`  | `/point/{lon},{lat}`                                            | JSON ([Point][multipoint_model])                 | return pixel values from assets
| `GET`  | `/preview[.{format}]`                                           | image/bin                                        | create a preview image from assets (**Optional**)
| `GET`  | `/bbox/{minx},{miny},{maxx},{maxy}[/{width}x{height}].{format}` | image/bin                                        | create an image from part of assets (**Optional**)
| `POST` | `/feature[/{width}x{height}][.{format}]`                           | image/bin                                        | create an image from a geojson feature intersecting assets (**Optional**)
| `GET`  | `[/{tileMatrixSetId}]/map`                                      | HTML                                             | return a simple map viewer

## MultiBandTilerFactory

Custom `TilerFactory` to be used with [`rio_tiler.io.MultiBandReader`](https://cogeotiff.github.io/rio-tiler/advanced/custom_readers/#multibasereader) type readers.

#### Attributes

- **layer_dependency**: Dependency to define assets or expression. Defaults to `titiler.core.dependencies.BandsExprParams`.
- **bands_dependency**: Dependency to define bands to be used. Defaults to `titiler.core.dependencies.BandsParams`.

#### Endpoints

```python
from fastapi import FastAPI, Query
# rio_tiler_pds.landsat.aws.LandsatC2Reader is a MultiBandReader
from rio_tiler_pds.landsat.aws import LandsatC2Reader
from titiler.core.factory import MultiBandTilerFactory


def SceneIDParams(
    sceneid: Annotated[
        str,
        Query(description="Landsat Scene ID")
    ]
) -> str:
    """Use `sceneid` in query instead of url."""
    return sceneid


app = FastAPI()
landsat = MultiBandTilerFactory(reader=LandsatC2Reader, path_dependency=SceneIDParams)
app.include_router(landsat.router)
```

| Method | URL                                                             | Output                                       | Description
| ------ | --------------------------------------------------------------- |--------------------------------------------- |--------------
| `GET`  | `/bounds`                                                       | JSON ([Bounds][bounds_model])                | return dataset's bounds
| `GET`  | `/bands`                                                        | JSON                                         | return the list of available bands
| `GET`  | `/info`                                                         | JSON ([Info][info_model])                    | return basic info for a dataset
| `GET`  | `/info.geojson`                                                 | GeoJSON ([InfoGeoJSON][info_geojson_model])  | return basic info for a dataset as a GeoJSON feature
| `GET`  | `/statistics`                                                   | JSON ([Statistics][stats_model])             | return info and statistics for a dataset
| `POST` | `/statistics`                                                   | GeoJSON ([Statistics][stats_geojson_model])  | return info and statistics for a dataset
| `GET`  | `/tiles[/{tileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`  | image/bin                                    | create a web map tile image from a dataset
| `GET`  | `/[{tileMatrixSetId}]/tilejson.json`                            | JSON ([TileJSON][tilejson_model])            | return a Mapbox TileJSON document
| `GET`  | `/{tileMatrixSetId}/WMTSCapabilities.xml`                       | XML                                          | return OGC WMTS Get Capabilities
| `GET`  | `/point/{lon},{lat}`                                            | JSON ([Point][point_model])                  | return pixel value from a dataset
| `GET`  | `/preview[.{format}]`                                           | image/bin                                    | create a preview image from a dataset
| `GET`  | `/bbox/{minx},{miny},{maxx},{maxy}[/{width}x{height}].{format}` | image/bin                                    | create an image from part of a dataset
| `POST` | `/feature[/{width}x{height}][.{format}]`                           | image/bin                                    | create an image from a geojson feature
| `GET`  | `[/{tileMatrixSetId}]/map`                                      | HTML                                         | return a simple map viewer

## MosaicTilerFactory


In `titiler.mosaic.factory`, custom `TilerFactory`

#### Attributes

- **layer_dependency**: Dependency to define assets or expression. Defaults to `titiler.core.dependencies.BandsExprParams`.
- **bands_dependency**: Dependency to define bands to be used. Defaults to `titiler.core.dependencies.BandsParams`.

#### Endpoints

| Method | URL                                                             | Output                                             | Description
| ------ | --------------------------------------------------------------- |--------------------------------------------------- |--------------
| `GET`  | `/`                                                             | JSON [MosaicJSON][mosaic_model]                    | return a MosaicJSON document
| `GET`  | `/bounds`                                                       | JSON ([Bounds][bounds_model])                      | return mosaic's bounds
| `GET`  | `/info`                                                         | JSON ([Info][mosaic_info_model])                   | return mosaic's basic info
| `GET`  | `/info.geojson`                                                 | GeoJSON ([InfoGeoJSON][mosaic_geojson_info_model]) | return mosaic's basic info  as a GeoJSON feature
| `GET`  | `/tiles[/{tileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`  | image/bin                                          | create a web map tile image from a MosaicJSON
| `GET`  | `[/{tileMatrixSetId}]/tilejson.json`                            | JSON ([TileJSON][tilejson_model])                  | return a Mapbox TileJSON document
| `GET`  | `[/{tileMatrixSetId}]/WMTSCapabilities.xml`                     | XML                                                | return OGC WMTS Get Capabilities
| `GET`  | `/point/{lon},{lat}`                                            | JSON ([Point][mosaic_point])                       | return pixel value from a MosaicJSON dataset
| `GET`  | `/{z}/{x}/{y}/assets`                                           | JSON                                               | return list of assets intersecting a XYZ tile
| `GET`  | `/{lon},{lat}/assets`                                           | JSON                                               | return list of assets intersecting a point
| `GET`  | `/{minx},{miny},{maxx},{maxy}/assets`                           | JSON                                               | return list of assets intersecting a bounding box
| `GET`  | `[/{tileMatrixSetId}]/map`                                      | HTML                                               | return a simple map viewer


!!! Important

    **Factories** are built around [`rio_tiler.io.BaseReader`](https://cogeotiff.github.io/rio-tiler/advanced/custom_readers/), which defines basic methods to access datasets (e.g COG or STAC). The default reader is `Reader` for `TilerFactory` and `MosaicBackend` for `MosaicTilerFactory`.

    Factories classes use [dependencies injection](dependencies.md) to define most of the endpoint options.


[bounds_model]: https://github.com/cogeotiff/rio-tiler/blob/9aaa88000399ee8d36e71d176f67b6ea3ec53f2d/rio_tiler/models.py#L43-L46
[info_model]: https://github.com/cogeotiff/rio-tiler/blob/9aaa88000399ee8d36e71d176f67b6ea3ec53f2d/rio_tiler/models.py#L56-L72
[info_geojson_model]: https://github.com/developmentseed/titiler/blob/c97e251c46b51703d41b1c9e66bc584649aa231c/src/titiler/core/titiler/core/models/responses.py#L30
[tilejson_model]: https://github.com/developmentseed/titiler/blob/2335048a407f17127099cbbc6c14e1328852d619/src/titiler/core/titiler/core/models/mapbox.py#L16-L38
[point_model]: https://github.com/developmentseed/titiler/blob/c97e251c46b51703d41b1c9e66bc584649aa231c/src/titiler/core/titiler/core/models/responses.py#L11-L20
[stats_model]: https://github.com/developmentseed/titiler/blob/c97e251c46b51703d41b1c9e66bc584649aa231c/src/titiler/core/titiler/core/models/responses.py#L32
[stats_geojson_model]: https://github.com/developmentseed/titiler/blob/c97e251c46b51703d41b1c9e66bc584649aa231c/src/titiler/core/titiler/core/models/responses.py#L46-L49

[multiinfo_model]: https://github.com/developmentseed/titiler/blob/c97e251c46b51703d41b1c9e66bc584649aa231c/src/titiler/core/titiler/core/models/responses.py#L52
[multiinfo_geojson_model]: https://github.com/developmentseed/titiler/blob/c97e251c46b51703d41b1c9e66bc584649aa231c/src/titiler/core/titiler/core/models/responses.py#L53
[multipoint_model]: https://github.com/developmentseed/titiler/blob/c97e251c46b51703d41b1c9e66bc584649aa231c/src/titiler/core/titiler/core/models/responses.py#L23-L27
[multistats_model]: https://github.com/developmentseed/titiler/blob/c97e251c46b51703d41b1c9e66bc584649aa231c/src/titiler/core/titiler/core/models/responses.py#L55
[multistats_geojson_model]: https://github.com/developmentseed/titiler/blob/c97e251c46b51703d41b1c9e66bc584649aa231c/src/titiler/core/titiler/core/models/responses.py#L56-L59

[mosaic_info_model]: https://github.com/developmentseed/cogeo-mosaic/blob/1dc3c873472c8cf7634ad893b9cdc40105ca3874/cogeo_mosaic/models.py#L9-L17
[mosaic_geojson_info_model]: https://github.com/developmentseed/titiler/blob/2bd1b159a9cf0932ad14e9eabf1e4e66498adbdc/src/titiler/mosaic/titiler/mosaic/factory.py#L130
[mosaic_model]: https://github.com/developmentseed/cogeo-mosaic/blob/1dc3c873472c8cf7634ad893b9cdc40105ca3874/cogeo_mosaic/mosaic.py#L55-L72
[mosaic_point]: https://github.com/developmentseed/titiler/blob/2bd1b159a9cf0932ad14e9eabf1e4e66498adbdc/src/titiler/mosaic/titiler/mosaic/models/responses.py#L8-L17
