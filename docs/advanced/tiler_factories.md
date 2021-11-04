
Tiler factories are helper functions that let users create a FastAPI router (`fastapi.APIRouter`) with a minimal set of endpoints.

### `titiler.core.factory.TilerFactory`

```python
from fastapi import FastAPI

from titiler.core.factory import TilerFactory

app = FastAPI(description="A lightweight Cloud Optimized GeoTIFF tile server")
cog = TilerFactory()
app.include_router(cog.router, tags=["Cloud Optimized GeoTIFF"])
```

| Method | URL                                                             | Output                                      | Description
| ------ | --------------------------------------------------------------- |-------------------------------------------- |--------------
| `GET`  | `/bounds`                                                       | JSON ([Bounds][bounds_model])               | return dataset's bounds
| `GET`  | `/info`                                                         | JSON ([Info][info_model])                   | return dataset's basic info
| `GET`  | `/info.geojson`                                                 | GeoJSON ([InfoGeoJSON][geoinfo_model])      | return dataset's basic info as a GeoJSON feature
| `GET`  | `/statistics`                                                   | JSON ([Statistics][stats_model])            | return dataset's statistics
| `POST` | `/statistics`                                                   | GeoJSON ([Statistics][stats_geojson_model]) | return dataset's statistics for a GeoJSON
| `GET`  | `/tiles/[{TileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`  | image/bin                                   | create a web map tile image from a dataset
| `GET`  | `/[{TileMatrixSetId}]/tilejson.json`                            | JSON ([TileJSON][tilejson_model])           | return a Mapbox TileJSON document
| `GET`  | `/{TileMatrixSetId}/WMTSCapabilities.xml`                       | XML                                         | return OGC WMTS Get Capabilities
| `GET`  | `/point/{lon},{lat}`                                            | JSON ([Point][point_model])                 | return pixel value from a dataset
| `GET`  | `/preview[.{format}]`                                           | image/bin                                   | create a preview image from a dataset
| `GET`  | `/crop/{minx},{miny},{maxx},{maxy}[/{width}x{height}].{format}` | image/bin                                   | create an image from part of a dataset
| `POST` | `/crop[/{width}x{height}][.{format}]`                           | image/bin                                   | create an image from a GeoJSON feature

### `titiler.core.factory.MultiBaseTilerFactory`

Custom `TilerFactory` to be used with `rio_tiler.io.MultiBaseReader` type readers.

```python
from fastapi import FastAPI
from rio_tiler.io import STACReader # rio_tiler.io.STACReader is a MultiBaseReader

from titiler.core.factory import MultiBaseTilerFactory

app = FastAPI(description="A lightweight STAC tile server")
cog = MultiBaseTilerFactory(reader=STACReader)
app.include_router(cog.router, tags=["STAC"])
```

| Method | URL                                                             | Output    | Description
| ------ | --------------------------------------------------------------- |---------- |--------------
| `GET`  | `/bounds`                                                       | JSON      | return dataset's bounds
| `GET`  | `/assets`                                                       | JSON      | return the list of available assets
| `GET`  | `/info`                                                         | JSON      | return assets basic info
| `GET`  | `/info.geojson`                                                 | GeoJSON   | return assets basic info as a GeoJSON feature
| `GET`  | `/statistics`                                                   | JSON      | return assets statistics
| `POST` | `/statistics`                                                   | GeoJSON   | return assets statistics for a GeoJSON
| `GET`  | `/tiles/[{TileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`  | image/bin | create a web map tile image from assets
| `GET`  | `/[{TileMatrixSetId}]/tilejson.json`                            | JSON      | return a Mapbox TileJSON document
| `GET`  | `/{TileMatrixSetId}/WMTSCapabilities.xml`                       | XML       | return OGC WMTS Get Capabilities
| `GET`  | `/point/{lon},{lat}`                                            | JSON      | return pixel value from assets
| `GET`  | `/preview[.{format}]`                                           | image/bin | create a preview image from assets
| `GET`  | `/crop/{minx},{miny},{maxx},{maxy}[/{width}x{height}].{format}` | image/bin | create an image from part of assets
| `POST` | `/crop[/{width}x{height}][.{format}]`                           | image/bin | create an image from a geojson feature intersecting assets

### `titiler.core.factory.MultiBandTilerFactory`

Custom `TilerFactory` to be used with `rio_tiler.io.MultiBandReader` type readers.

```python
from fastapi import FastAPI, Query
from rio_tiler_pds.landsat.aws import LandsatC2Reader # rio_tiler_pds.landsat.aws.LandsatC2Reader is a MultiBandReader

from titiler.core.factory import MultiBandTilerFactory


def SceneIDParams(sceneid: str = Query(..., description="Landsat Scene ID")) -> str:
    """Use `sceneid` in query instead of url."""
    return sceneid


app = FastAPI(description="A lightweight Landsat Collection 2 tile server")
cog = MultiBandTilerFactory(reader=LandsatC2Reader, path_dependency=SceneIDParams)
app.include_router(cog.router, tags=["Landsat"])
```

| Method | URL                                                             | Output    | Description
| ------ | --------------------------------------------------------------- |---------- |--------------
| `GET`  | `/bounds`                                                       | JSON      | return dataset's bounds
| `GET`  | `/bands`                                                        | JSON      | return the list of available bands
| `GET`  | `/info`                                                         | JSON      | return basic info for a dataset
| `GET`  | `/info.geojson`                                                 | GeoJSON   | return basic info for a dataset as a GeoJSON feature
| `GET`  | `/statistics`                                                   | JSON      | return info and statistics for a dataset
| `POST` | `/statistics`                                                   | GeoJSON   | return info and statistics for a dataset
| `GET`  | `/tiles/[{TileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`  | image/bin | create a web map tile image from a dataset
| `GET`  | `/[{TileMatrixSetId}]/tilejson.json`                            | JSON      | return a Mapbox TileJSON document
| `GET`  | `/{TileMatrixSetId}/WMTSCapabilities.xml`                       | XML       | return OGC WMTS Get Capabilities
| `GET`  | `/point/{lon},{lat}`                                            | JSON      | return pixel value from a dataset
| `GET`  | `/preview[.{format}]`                                           | image/bin | create a preview image from a dataset
| `GET`  | `/crop/{minx},{miny},{maxx},{maxy}[/{width}x{height}].{format}` | image/bin | create an image from part of a dataset
| `POST` | `/crop[/{width}x{height}][.{format}]`                           | image/bin | create an image from a geojson feature


### `titiler.mosaic.factory.MosaicTilerFactory`


| Method | URL                                                             | Output    | Description
| ------ | --------------------------------------------------------------- |---------- |--------------
| `GET`  | `/`                                                             | JSON      | return a MosaicJSON document
| `GET`  | `/bounds`                                                       | JSON      | return bounds info for a MosaicJSON
| `GET`  | `/info`                                                         | JSON      | return basic info for a MosaicJSON
| `GET`  | `/info.geojson`                                                 | GeoJSON   | return basic info for a MosaicJSON as a GeoJSON feature
| `GET`  | `/tiles/[{TileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`  | image/bin | create a web map tile image from a MosaicJSON
| `GET`  | `/[{TileMatrixSetId}]/tilejson.json`                            | JSON      | return a Mapbox TileJSON document
| `GET`  | `/{TileMatrixSetId}/WMTSCapabilities.xml`                       | XML       | return OGC WMTS Get Capabilities
| `GET`  | `/point/{lon},{lat}`                                            | JSON      | return pixel value from a MosaicJSON dataset
| `GET`  | `/{z}/{x}/{y}/assets`                                           | JSON      | return list of assets intersecting a XYZ tile
| `GET`  | `/{lon},{lat}/assets`                                           | JSON      | return list of assets intersecting a point
| `GET`  | `/{minx},{miny},{maxx},{maxy}/assets`                           | JSON      | return list of assets intersecting a bounding box


## FYI

**Factories** are built around [`rio_tiler.io.BaseReader`](https://cogeotiff.github.io/rio-tiler/advanced/custom_readers/), which defines basic methods to access datasets (e.g COG or STAC). The default reader is `COGReader` for `TilerFactory` and `MosaicBackend` for `MosaicTilerFactory`.

Factories classes use [dependencies injection](dependencies.md) to define most of the endpoint options.


[bounds_model]: https://github.com/cogeotiff/rio-tiler/blob/9aaa88000399ee8d36e71d176f67b6ea3ec53f2d/rio_tiler/models.py#L43-L46
[info_model]: https://github.com/cogeotiff/rio-tiler/blob/9aaa88000399ee8d36e71d176f67b6ea3ec53f2d/rio_tiler/models.py#L56-L72
[tilejson_model]: https://github.com/developmentseed/titiler/blob/2335048a407f17127099cbbc6c14e1328852d619/src/titiler/core/titiler/core/models/mapbox.py#L16-L38

[point_model]: https://github.com/developmentseed/titiler/blob/2335048a407f17127099cbbc6c14e1328852d619/src/titiler/core/titiler/core/models/mapbox.py#L16-L38
[geoinfo_model]: https://github.com/developmentseed/titiler/blob/2335048a407f17127099cbbc6c14e1328852d619/src/titiler/core/titiler/core/models/mapbox.py#L16-L38
[stats_model]: https://github.com/developmentseed/titiler/blob/2335048a407f17127099cbbc6c14e1328852d619/src/titiler/core/titiler/core/models/mapbox.py#L16-L38
[stats_geojson_model]: https://github.com/developmentseed/titiler/blob/2335048a407f17127099cbbc6c14e1328852d619/src/titiler/core/titiler/core/models/mapbox.py#L16-L38
