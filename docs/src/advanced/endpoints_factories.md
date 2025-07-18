
TiTiler's endpoints factories are helper functions that let users create a FastAPI *router* (`fastapi.APIRouter`) with a minimal set of endpoints.

!!! Important

    Most of `tiler` **Factories** are built around [`rio_tiler.io.BaseReader`](https://cogeotiff.github.io/rio-tiler/advanced/custom_readers/), which defines basic methods to access datasets (e.g COG or STAC). The default reader is `Reader` for `TilerFactory` and `MosaicBackend` for `MosaicTilerFactory`.

    Factories classes use [dependencies injection](dependencies.md) to define most of the endpoint options.

## titiler.core

### BaseFactory

class: `titiler.core.factory.BaseFactory`

Most **Factories** are built from this [abstract based class](https://docs.python.org/3/library/abc.html) which is used to define commons attributes and utility functions shared between all factories.

#### Attributes

- **router**: FastAPI router. Defaults to `fastapi.APIRouter`.
- **router_prefix**: Set prefix to all factory's endpoint. Defaults to `""`.
- **route_dependencies**: Additional routes dependencies to add after routes creations. Defaults to `[]`.
- **extension**: TiTiler extensions to register after endpoints creations. Defaults to `[]`.
- **name**: Name of the Endpoints group. Defaults to `None`.
- **operation_prefix** (*private*): Endpoint's `operationId` prefix. Defined by `self.name` or `self.router_prefix.replace("/", ".")`.
- **conforms_to**: Set of conformance classes the Factory implement

#### Methods

- **register_routes**: Abstract method which needs to be define by each factories.
- **url_for**: Method to construct endpoint URL
- **add_route_dependencies**: Add dependencies to routes.

### TilerFactory

class: `titiler.core.factory.TilerFactory`

Factory meant to create endpoints for single dataset using [*rio-tiler*'s `Reader`](https://cogeotiff.github.io/rio-tiler/readers/#rio_tileriorasterioreader).

#### Attributes

- **reader**: Dataset Reader **required**.
- **reader_dependency**: Dependency to control options passed to the reader instance init. Defaults to `titiler.core.dependencies.DefaultDependency`
- **path_dependency**: Dependency to use to define the dataset url. Defaults to `titiler.core.dependencies.DatasetPathParams`.
- **layer_dependency**: Dependency to define band indexes or expression. Defaults to `titiler.core.dependencies.BidxExprParams`.
- **dataset_dependency**: Dependency to overwrite `nodata` value, apply `rescaling` and change the `I/O` or `Warp` resamplings. Defaults to `titiler.core.dependencies.DatasetParams`.
- **tile_dependency**: Dependency to define `buffer` and `padding` to apply at tile creation. Defaults to `titiler.core.dependencies.TileParams`.
- **stats_dependency**: Dependency to define options for *rio-tiler*'s statistics method used in `/statistics` endpoints. Defaults to `titiler.core.dependencies.StatisticsParams`.
- **histogram_dependency**: Dependency to define *numpy*'s histogram options used in `/statistics` endpoints. Defaults to `titiler.core.dependencies.HistogramParams`.
- **img_preview_dependency**: Dependency to define image size for `/preview` and `/statistics` endpoints. Defaults to `titiler.core.dependencies.PreviewParams`.
- **img_part_dependency**: Dependency to define image size for `/bbox` and `/feature` endpoints. Defaults to `titiler.core.dependencies.PartFeatureParams`.
- **process_dependency**: Dependency to control which `algorithm` to apply to the data. Defaults to `titiler.core.algorithm.algorithms.dependency`.
- **colormap_dependency**: Dependency to define the Colormap options. Defaults to `titiler.core.dependencies.ColorMapParams`
- **render_dependency**: Dependency to control output image rendering options. Defaults to `titiler.core.dependencies.ImageRenderingParams`
- **environment_dependency**: Dependency to define GDAL environment at runtime. Default to `lambda: {}`.
- **supported_tms**: List of available TileMatrixSets. Defaults to `morecantile.tms`.
- **templates**: *Jinja2* templates to use in endpoints. Defaults to `titiler.core.factory.DEFAULT_TEMPLATES`.
- **render_func**: Image rendering method. Defaults to `titiler.core.utils.render_image`.
- **add_preview**: Add `/preview` endpoint to the router. Defaults to `True`.
- **add_part**: Add `/bbox` and `/feature` endpoints to the router. Defaults to `True`.
- **add_viewer**: Add `/{TileMatrixSetId}/map.html` endpoints to the router. Defaults to `True`.
- **add_ogc_maps**: Add `/map` endoint (OGC Maps API) to the router. Defaults to `False`.

#### Endpoints

```python
from fastapi import FastAPI

from titiler.core.factory import TilerFactory

# Create FastAPI application
app = FastAPI()

# Create router and register set of endpoints
cog = TilerFactory(
    add_preview=True,
    add_part=True,
    add_viewer=True,
    add_ogc_maps=True,
)

# add router endpoint to the main application
app.include_router(cog.router)
```

| Method | URL                                                             | Output                                      | Description
| ------ | --------------------------------------------------------------- |-------------------------------------------- |--------------
| `GET`  | `/bounds`                                                       | JSON ([Bounds][bounds_model])               | return dataset's bounds
| `GET`  | `/info`                                                         | JSON ([Info][info_model])                   | return dataset's basic info
| `GET`  | `/info.geojson`                                                 | GeoJSON ([InfoGeoJSON][info_geojson_model]) | return dataset's basic info as a GeoJSON feature
| `GET`  | `/statistics`                                                   | JSON ([Statistics][stats_model])            | return dataset's statistics
| `POST` | `/statistics`                                                   | GeoJSON ([Statistics][stats_geojson_model]) | return dataset's statistics for a GeoJSON
| `GET`  | `/tiles`                                                        | JSON                                        | List of OGC Tilesets available
| `GET`  | `/tiles/{tileMatrixSetId}`                                      | JSON                                        | OGC Tileset metadata
| `GET`  | `/tiles/{tileMatrixSetId}/{z}/{x}/{y}[@{scale}x][.{format}]`    | image/bin                                   | create a web map tile image from a dataset
| `GET`  | `/{tileMatrixSetId}/map.html`                                   | HTML                                        | return a simple map viewer **Optional**
| `GET`  | `/{tileMatrixSetId}/tilejson.json`                              | JSON ([TileJSON][tilejson_model])           | return a Mapbox TileJSON document
| `GET`  | `/{tileMatrixSetId}/WMTSCapabilities.xml`                       | XML                                         | return OGC WMTS Get Capabilities
| `GET`  | `/point/{lon},{lat}`                                            | JSON ([Point][point_model])                 | return pixel values from a dataset
| `GET`  | `/bbox/{minx},{miny},{maxx},{maxy}[/{width}x{height}].{format}` | image/bin                                   | create an image from part of a dataset **Optional**
| `POST` | `/feature[/{width}x{height}][.{format}]`                        | image/bin                                   | create an image from a GeoJSON feature **Optional**
| `GET`  | `/preview[/{width}x{height}][.{format}]`                        | image/bin                                   | create a preview image from a dataset **Optional**
| `GET`  | `/maps`                                                         | image/bin                                   | create maps from a dataset **Optional**


### MultiBaseTilerFactory

class: `titiler.core.factory.MultiBaseTilerFactory`

Custom `TilerFactory` to be used with [`rio_tiler.io.MultiBaseReader`](https://cogeotiff.github.io/rio-tiler/advanced/custom_readers/#multibasereader) type readers (e.g [`rio_tiler.io.STACReader`](https://cogeotiff.github.io/rio-tiler/readers/#rio_tileriostacstacreader)).

#### Attributes

- **reader**: `rio_tiler.io.base.MultiBaseReader` Dataset Reader **required**.
- **layer_dependency**: Dependency to define assets or expression. Defaults to `titiler.core.dependencies.AssetsBidxExprParams`.
- **assets_dependency**: Dependency to define assets to be used. Defaults to `titiler.core.dependencies.AssetsParams`.

#### Endpoints

```python
from fastapi import FastAPI

from rio_tiler.io import STACReader  # STACReader is a MultiBaseReader

from titiler.core.factory import MultiBaseTilerFactory

app = FastAPI()
stac = MultiBaseTilerFactory(
    reader=STACReader,
    add_preview=True,
    add_part=True,
    add_viewer=True,
    add_ogc_maps=True,
)
app.include_router(stac.router)
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
| `GET`  | `/tiles`                                                        | JSON                                             | List of OGC Tilesets available
| `GET`  | `/tiles/{tileMatrixSetId}`                                      | JSON                                             | OGC Tileset metadata
| `GET`  | `/tiles/{tileMatrixSetId}/{z}/{x}/{y}[@{scale}x][.{format}]`    | image/bin                                        | create a web map tile image from assets
| `GET`  | `/{tileMatrixSetId}/map.html`                                   | HTML                                             | return a simple map viewer **Optional**
| `GET`  | `/{tileMatrixSetId}/tilejson.json`                              | JSON ([TileJSON][tilejson_model])                | return a Mapbox TileJSON document
| `GET`  | `/{tileMatrixSetId}/WMTSCapabilities.xml`                       | XML                                              | return OGC WMTS Get Capabilities
| `GET`  | `/point/{lon},{lat}`                                            | JSON ([Point][multipoint_model])                 | return pixel values from assets
| `GET`  | `/bbox/{minx},{miny},{maxx},{maxy}[/{width}x{height}].{format}` | image/bin                                        | create an image from part of assets **Optional**
| `POST` | `/feature[/{width}x{height}][.{format}]`                        | image/bin                                        | create an image from a geojson feature intersecting assets **Optional**
| `GET`  | `/preview[/{width}x{height}][.{format}]`                        | image/bin                                        | create a preview image from assets **Optional**
| `GET`  | `/map`                                                         | image/bin                                        | create maps from a dataset **Optional**

### MultiBandTilerFactory

class: `titiler.core.factory.MultiBandTilerFactory`

Custom `TilerFactory` to be used with [`rio_tiler.io.MultiBandReader`](https://cogeotiff.github.io/rio-tiler/advanced/custom_readers/#multibandsreader) type readers.

#### Attributes

- **reader**: `rio_tiler.io.base.MultiBandReader` Dataset Reader **required**.
- **layer_dependency**: Dependency to define assets or expression. Defaults to `titiler.core.dependencies.BandsExprParams`.
- **bands_dependency**: Dependency to define bands to be used. Defaults to `titiler.core.dependencies.BandsParams`.

#### Endpoints

```python
from fastapi import FastAPI, Query


from rio_tiler_pds.landsat.aws import LandsatC2Reader  # LandsatC2Reader is a MultiBandReader
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
| `GET`  | `/tiles`                                                        | JSON                                         | List of OGC Tilesets available
| `GET`  | `/tiles/{tileMatrixSetId}`                                      | JSON                                         | OGC Tileset metadata
| `GET`  | `/tiles/{tileMatrixSetId}/{z}/{x}/{y}[@{scale}x][.{format}]`    | image/bin                                    | create a web map tile image from a dataset
| `GET`  | `/{tileMatrixSetId}/map.html`                                   | HTML                                         | return a simple map viewer **Optional**
| `GET`  | `/{tileMatrixSetId}/tilejson.json`                              | JSON ([TileJSON][tilejson_model])            | return a Mapbox TileJSON document
| `GET`  | `/{tileMatrixSetId}/WMTSCapabilities.xml`                       | XML                                          | return OGC WMTS Get Capabilities
| `GET`  | `/point/{lon},{lat}`                                            | JSON ([Point][point_model])                  | return pixel value from a dataset
| `GET`  | `/bbox/{minx},{miny},{maxx},{maxy}[/{width}x{height}].{format}` | image/bin                                    | create an image from part of a dataset **Optional**
| `POST` | `/feature[/{width}x{height}][.{format}]`                        | image/bin                                    | create an image from a geojson feature **Optional**
| `GET`  | `/preview[/{width}x{height}][.{format}]`                        | image/bin                                    | create a preview image from a dataset **Optional**
| `GET`  | `/map`                                                         | image/bin                                    | create maps from a dataset **Optional**


### TMSFactory

class: `titiler.core.factory.TMSFactory`

Endpoints factory for OGC `TileMatrixSets`.

#### Attributes

- **supported_tms**: List of available TileMatrixSets. Defaults to `morecantile.tms`.

```python
from fastapi import FastAPI

from titiler.core.factory import TMSFactory

app = FastAPI()
tms = TMSFactory()
app.include_router(tms.router)
```

#### Endpoints

| Method | URL                                   | Output                                         | Description
| ------ | ------------------------------------- |----------------------------------------------- |--------------
| `GET`  | `/tileMatrixSets`                     | JSON ([TileMatrixSetList][tilematrixset_list]) | retrieve the list of available tiling schemes (tile matrix sets)
| `GET`  | `/tileMatrixSets/{tileMatrixSetId}`   | JSON ([TileMatrixSet][tilematrixset])          | retrieve the definition of the specified tiling scheme (tile matrix set)


### AlgorithmFactory

class: `titiler.core.factory.AlgorithmFactory`

Endpoints factory for custom algorithms.

#### Attributes

- **supported_algorithm**: List of available `Algorithm`. Defaults to `titiler.core.algorithm.algorithms`.

```python
from fastapi import FastAPI

from titiler.core.factory import AlgorithmFactory

app = FastAPI()
algo = AlgorithmFactory()
app.include_router(algo.router)
```

#### Endpoints

| Method | URL                          | Output                                                   | Description
| ------ | ---------------------------- |--------------------------------------------------------- |--------------
| `GET`  | `/algorithms`                | JSON (Dict of [Algorithm Metadata][algorithm_metadata])            | retrieve the list of available Algorithms
| `GET`  | `/algorithms/{algorithmId}`  | JSON ([Algorithm Metadata][algorithm_metadata])                    | retrieve the metadata of the specified algorithm.


### ColorMapFactory

class: `titiler.core.factory.ColorMapFactory`

Endpoints factory for colorMaps metadata.

#### Attributes

- **supported_colormaps**: List of available `ColorMaps`. Defaults to `rio_tiler.colormap.cmap`.

```python
from fastapi import FastAPI

from titiler.core.factory import ColorMapFactory

app = FastAPI()
colormap = ColorMapFactory()
app.include_router(colormap.router)
```

#### Endpoints

| Method | URL                          | Output                                | Description
| ------ | ---------------------------- |-------------------------------------- |--------------
| `GET`  | `/colorMaps`                 | JSON ([colorMapList][colormap_list])  | retrieve the list of available colorMaps
| `GET`  | `/colorMaps/{colorMapId}`    | JSON ([colorMap][colormap])           | retrieve the metadata or image of the specified colorMap.


## titiler.mosaic

### MosaicTilerFactory

class: `titiler.mosaic.factory.MosaicTilerFactory`

Endpoints factory for mosaics, built on top of [MosaicJSON](https://github.com/developmentseed/mosaicjson-spec).

#### Attributes

- **backend**: `cogeo_mosaic.backends.BaseBackend` Mosaic backend. Defaults to `cogeo_mosaic.backend.MosaicBackend`.
- **backend_dependency**: Dependency to control options passed to the backend instance init. Defaults to `titiler.core.dependencies.DefaultDependency`
- **dataset_reader**: Dataset Reader. Defaults to `rio_tiler.io.Reader`
- **reader_dependency**: Dependency to control options passed to the reader instance init. Defaults to `titiler.core.dependencies.DefaultDependency`
- **path_dependency**: Dependency to use to define the dataset url. Defaults to `titiler.mosaic.factory.DatasetPathParams`.
- **assets_accessor_dependency**: Dependency to define options to be forwarded to the backend `get_assets` method. Defaults to `titiler.core.dependencies.DefaultDependency`.
- **layer_dependency**: Dependency to define band indexes or expression. Defaults to `titiler.core.dependencies.BidxExprParams`.
- **dataset_dependency**: Dependency to overwrite `nodata` value, apply `rescaling` and change the `I/O` or `Warp` resamplings. Defaults to `titiler.core.dependencies.DatasetParams`.
- **tile_dependency**: Dependency to define `buffer` and `padding` to apply at tile creation. Defaults to `titiler.core.dependencies.TileParams`.
- **process_dependency**: Dependency to control which `algorithm` to apply to the data. Defaults to `titiler.core.algorithm.algorithms.dependency`.
- **colormap_dependency**: Dependency to define the Colormap options. Defaults to `titiler.core.dependencies.ColorMapParams`
- **render_dependency**: Dependency to control output image rendering options. Defaults to `titiler.core.dependencies.ImageRenderingParams`
- **pixel_selection_dependency**: Dependency to select the `pixel_selection` method. Defaults to `titiler.mosaic.factory.PixelSelectionParams`.
- **environment_dependency**: Dependency to define GDAL environment at runtime. Default to `lambda: {}`.
- **supported_tms**: List of available TileMatrixSets. Defaults to `morecantile.tms`.
- **supported_tms**: List of available TileMatrixSets. Defaults to `morecantile.tms`.
- **templates**: *Jinja2* templates to use in endpoints. Defaults to `titiler.core.factory.DEFAULT_TEMPLATES`.
- **optional_headers**: List of OptionalHeader which endpoints could add (if implemented). Defaults to `[]`.
- **add_viewer**: Add `/{TileMatrixSetId}/map.html` endpoints to the router. Defaults to `True`.

#### Endpoints

| Method | URL                                                             | Output                                             | Description
| ------ | --------------------------------------------------------------- |--------------------------------------------------- |--------------
| `GET`  | `/`                                                             | JSON [MosaicJSON][mosaic_model]                    | return a MosaicJSON document
| `GET`  | `/bounds`                                                       | JSON ([Bounds][bounds_model])                      | return mosaic's bounds
| `GET`  | `/info`                                                         | JSON ([Info][mosaic_info_model])                   | return mosaic's basic info
| `GET`  | `/info.geojson`                                                 | GeoJSON ([InfoGeoJSON][mosaic_geojson_info_model]) | return mosaic's basic info  as a GeoJSON feature
| `GET`  | `/tiles`                                                        | JSON                                               | List of OGC Tilesets available
| `GET`  | `/tiles/{tileMatrixSetId}`                                      | JSON                                               | OGC Tileset metadata
| `GET`  | `/tiles/{tileMatrixSetId}/{z}/{x}/{y}[@{scale}x][.{format}]`    | image/bin                                          | create a web map tile image from a MosaicJSON
| `GET`  | `/tiles/{tileMatrixSetId}/{z}/{x}/{y}/assets`                   | JSON                                               | return list of assets intersecting a XYZ tile
| `GET`  | `/{tileMatrixSetId}/map.html`                                   | HTML                                               | return a simple map viewer **Optional**
| `GET`  | `/{tileMatrixSetId}/tilejson.json`                              | JSON ([TileJSON][tilejson_model])                  | return a Mapbox TileJSON document
| `GET`  | `/{tileMatrixSetId}/WMTSCapabilities.xml`                       | XML                                                | return OGC WMTS Get Capabilities
| `GET`  | `/point/{lon},{lat}`                                            | JSON ([Point][mosaic_point])                       | return pixel value from a MosaicJSON dataset
| `GET`  | `/point/{lon},{lat}/assets`                                     | JSON                                               | return list of assets intersecting a point
| `GET`  | `/bbox/{minx},{miny},{maxx},{maxy}/assets`                      | JSON                                               | return list of assets intersecting a bounding box

## titiler.xarray

### TilerFactory

class: `titiler.xarray.factory.TilerFactory`

#### Attributes

- **reader**: Dataset Reader **required**.
- **path_dependency**: Dependency to use to define the dataset url. Defaults to `titiler.core.dependencies.DatasetPathParams`.
- **reader_dependency**: Dependency to control options passed to the reader instance init. Defaults to `titiler.xarray.dependencies.XarrayParams`
- **layer_dependency**: Dependency to define band indexes or expression. Defaults to `titiler.core.dependencies.BidxParams`.
- **dataset_dependency**: Dependency to overwrite `nodata` value and change the `Warp` resamplings. Defaults to `titiler.xarray.dependencies.DatasetParams`.
- **tile_dependency**: Dependency for tile creation options. Defaults to `titiler.core.dependencies.DefaultDependency`.
- **stats_dependency**: Dependency to define options for *rio-tiler*'s statistics method used in `/statistics` endpoints. Defaults to `titiler.core.dependencies.StatisticsParams`.
- **histogram_dependency**: Dependency to define *numpy*'s histogram options used in `/statistics` endpoints. Defaults to `titiler.core.dependencies.HistogramParams`.
- **img_part_dependency**: Dependency to define image size for `/bbox` and `/feature` endpoints. Defaults to `titiler.xarray.dependencies.PartFeatureParams`.
- **process_dependency**: Dependency to control which `algorithm` to apply to the data. Defaults to `titiler.core.algorithm.algorithms.dependency`.
- **colormap_dependency**: Dependency to define the Colormap options. Defaults to `titiler.core.dependencies.ColorMapParams`
- **render_dependency**: Dependency to control output image rendering options. Defaults to `titiler.core.dependencies.ImageRenderingParams`
- **environment_dependency**: Dependency to define GDAL environment at runtime. Default to `lambda: {}`.
- **supported_tms**: List of available TileMatrixSets. Defaults to `morecantile.tms`.
- **templates**: *Jinja2* templates to use in endpoints. Defaults to `titiler.core.factory.DEFAULT_TEMPLATES`.
- **add_part**: Add `/bbox` and `/feature` endpoints to the router. Defaults to `True`.
- **add_viewer**: Add `/{TileMatrixSetId}/map.html` endpoints to the router. Defaults to `True`.


```python
from fastapi import FastAPI

from titiler.xarray.factory import TilerFactory

# Create FastAPI application
app = FastAPI()

# Create router and register set of endpoints
md = TilerFactory(
    add_part=True,
    add_viewer=True,
)

# add router endpoint to the main application
app.include_router(md.router)
```

#### Endpoints

| Method | URL                                                             | Output                                      | Description
| ------ | --------------------------------------------------------------- |-------------------------------------------- |--------------
| `GET`  | `/bounds`                                                       | JSON ([Bounds][bounds_model])               | return dataset's bounds
| `GET`  | `/info`                                                         | JSON ([Info][info_model])                   | return dataset's basic info
| `GET`  | `/info.geojson`                                                 | GeoJSON ([InfoGeoJSON][info_geojson_model]) | return dataset's basic info as a GeoJSON feature
| `POST` | `/statistics`                                                   | GeoJSON ([Statistics][stats_geojson_model]) | return dataset's statistics for a GeoJSON
| `GET`  | `/tiles`                                                        | JSON                                        | List of OGC Tilesets available
| `GET`  | `/tiles/{tileMatrixSetId}`                                      | JSON                                        | OGC Tileset metadata
| `GET`  | `/tiles/{tileMatrixSetId}/{z}/{x}/{y}[@{scale}x][.{format}]`    | image/bin                                   | create a web map tile image from a dataset
| `GET`  | `/{tileMatrixSetId}/map.html`                                   | HTML                                        | return a simple map viewer **Optional**
| `GET`  | `/{tileMatrixSetId}/tilejson.json`                              | JSON ([TileJSON][tilejson_model])           | return a Mapbox TileJSON document
| `GET`  | `/{tileMatrixSetId}/WMTSCapabilities.xml`                       | XML                                         | return OGC WMTS Get Capabilities
| `GET`  | `/point/{lon},{lat}`                                            | JSON ([Point][point_model])                 | return pixel values from a dataset
| `GET`  | `/bbox/{minx},{miny},{maxx},{maxy}[/{width}x{height}].{format}` | image/bin                                   | create an image from part of a dataset **Optional**
| `POST` | `/feature[/{width}x{height}][.{format}]`                        | image/bin                                   | create an image from a GeoJSON feature **Optional**


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

[tilematrixset_list]: https://github.com/developmentseed/titiler/blob/ffd67af34c2807a6e1447817f943446a58441ed8/src/titiler/core/titiler/core/models/OGC.py#L33-L40
[tilematrixset]: https://github.com/developmentseed/morecantile/blob/eec54326ce2b134cfbc03dd69a3e2938e4109101/morecantile/models.py#L399-L490

[algorithm_metadata]: https://github.com/developmentseed/titiler/blob/ffd67af34c2807a6e1447817f943446a58441ed8/src/titiler/core/titiler/core/algorithm/base.py#L32-L40

[colormap_list]: https://github.com/developmentseed/titiler/blob/535304fd7e1b0bfbb791bdec8cbfb6e78b4a6eb5/src/titiler/core/titiler/core/models/responses.py#L51-L55
[colormap]: https://github.com/cogeotiff/rio-tiler/blob/6343b571a367ef63a10d6807e3d907c3283ebb20/rio_tiler/types.py#L24-L27
