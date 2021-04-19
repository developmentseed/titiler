
Tiler factories are helper functions that let users create a FastAPI router (`fastapi.APIRouter`) with a minimal set of endpoints.

### `titiler.core.factory.TilerFactory`

```python
from fastapi import FastAPI

from titiler.core.factory import TilerFactory

app = FastAPI(description="A lightweight Cloud Optimized GeoTIFF tile server")
cog = TilerFactory()
app.include_router(cog.router, tags=["Cloud Optimized GeoTIFF"])
```

| Method | URL                                                             | Output    | Description
| ------ | --------------------------------------------------------------- |---------- |--------------
| `GET`  | `/bounds`                                                       | JSON      | return bounds info for a dataset
| `GET`  | `/info`                                                         | JSON      | return basic info for a dataset
| `GET`  | `/info.geojson`                                                 | GeoJSON   | return basic info for a dataset as a GeoJSON feature
| `GET`  | `/metadata`                                                     | JSON      | return info and statistics for a dataset
| `GET`  | `/tiles/[{TileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`  | image/bin | create a web map tile image from a dataset
| `GET`  | `/[{TileMatrixSetId}]/tilejson.json`                            | JSON      | return a Mapbox TileJSON document
| `GET`  | `/{TileMatrixSetId}/WMTSCapabilities.xml`                       | XML       | return OGC WMTS Get Capabilities
| `GET`  | `/point/{lon},{lat}`                                            | JSON      | return pixel value from a dataset
| `GET`  | `/preview[.{format}]`                                           | image/bin | **Optional** - create a preview image from a dataset
| `GET`  | `/crop/{minx},{miny},{maxx},{maxy}[/{width}x{height}].{format}` | image/bin | **Optional** - create an image from part of a dataset

### `titiler.core.factory.MultiBaseTilerFactory`

Custom `TilerFactory` to be used with `rio_tiler.io.MultiBaseReader` type readers.

```python
from fastapi import FastAPI
from rio_tiler.io import STACReader

from titiler.core.factory import MultiBaseTilerFactory

app = FastAPI(description="A lightweight STAC tile server")
cog = MultiBaseTilerFactory(reader=STACReader)
app.include_router(cog.router, tags=["STAC"])
```

| Method | URL                                                             | Output    | Description
| ------ | --------------------------------------------------------------- |---------- |--------------
| `GET`  | `/bounds`                                                       | JSON      | return bounds info for a dataset
| `GET`  | `/assets`                                                       | JSON      | return the list of available assets
| `GET`  | `/info`                                                         | JSON      | return basic info for a dataset
| `GET`  | `/info.geojson`                                                 | GeoJSON   | return basic info for a dataset as a GeoJSON feature
| `GET`  | `/metadata`                                                     | JSON      | return info and statistics for a dataset
| `GET`  | `/tiles/[{TileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`  | image/bin | create a web map tile image from a dataset
| `GET`  | `/[{TileMatrixSetId}]/tilejson.json`                            | JSON      | return a Mapbox TileJSON document
| `GET`  | `/{TileMatrixSetId}/WMTSCapabilities.xml`                       | XML       | return OGC WMTS Get Capabilities
| `GET`  | `/point/{lon},{lat}`                                            | JSON      | return pixel value from a dataset
| `GET`  | `/preview[.{format}]`                                           | image/bin | **Optional** - create a preview image from a dataset
| `GET`  | `/crop/{minx},{miny},{maxx},{maxy}[/{width}x{height}].{format}` | image/bin | **Optional** - create an image from part of a dataset

### `titiler.core.factory.MultiBandTilerFactory`

Custom `TilerFactory` to be used with `rio_tiler.io.MultiBandReader` type readers.

```python
from fastapi import FastAPI, Query
from rio_tiler_pds.landsat.aws import LandsatC2Reader

from titiler.core.factory import MultiBaseTilerFactory


def ScenePathParams(sceneid: str = Query(..., description="Landsat Scene ID")) -> str:
    """Create dataset path from args"""
    return url


app = FastAPI(description="A lightweight Landsat Collection 2 tile server")
cog = MultiBaseTilerFactory(reader=LandsatC2Reader, path_dependency=ScenePathParams)
app.include_router(cog.router, tags=["Landsat"])
```

| Method | URL                                                             | Output    | Description
| ------ | --------------------------------------------------------------- |---------- |--------------
| `GET`  | `/bounds`                                                       | JSON      | return bounds info for a dataset
| `GET`  | `/bands`                                                        | JSON      | return the list of available bands
| `GET`  | `/info`                                                         | JSON      | return basic info for a dataset
| `GET`  | `/info.geojson`                                                 | GeoJSON   | return basic info for a dataset as a GeoJSON feature
| `GET`  | `/metadata`                                                     | JSON      | return info and statistics for a dataset
| `GET`  | `/tiles/[{TileMatrixSetId}]/{z}/{x}/{y}[@{scale}x][.{format}]`  | image/bin | create a web map tile image from a dataset
| `GET`  | `/[{TileMatrixSetId}]/tilejson.json`                            | JSON      | return a Mapbox TileJSON document
| `GET`  | `/{TileMatrixSetId}/WMTSCapabilities.xml`                       | XML       | return OGC WMTS Get Capabilities
| `GET`  | `/point/{lon},{lat}`                                            | JSON      | return pixel value from a dataset
| `GET`  | `/preview[.{format}]`                                           | image/bin | **Optional** - create a preview image from a dataset
| `GET`  | `/crop/{minx},{miny},{maxx},{maxy}[/{width}x{height}].{format}` | image/bin | **Optional** - create an image from part of a dataset


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


## FYI

**Factories** are built around [`rio_tiler.io.BaseReader`](https://cogeotiff.github.io/rio-tiler/advanced/custom_readers/), which defines basic methods to access datasets (e.g COG or STAC). The default reader is `COGReader` for `TilerFactory` and `MosaicBackend` for `MosaicTilerFactory`.

Factories classes use [dependencies injection](dependencies.md) to define most of the endpoint options.
