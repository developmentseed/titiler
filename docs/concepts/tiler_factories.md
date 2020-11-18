
Tiler factories (`titiler.endpoints.factory.TilerFactory|MosaicTilerFactory`) are helper functions that let users create FastAPI router (`fastapi.APIRouter`).

```python
from titiler.endpoints.factory import TilerFactory

tiler = TilerFactory()

# Print defaults routes
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

All **factories** share a minimal route definition:

* `/bounds`: return dataset bounds
* `/info`: return dataset info (using `rio_tiler.models.Info` model)
* `/tiles/[{TileMatrixSetId}/]{z}/{x}/{y}[@{scale}x.{format}]`: return tile images
* `/tilesjon.json`: return a mapbox TileJSON document
* `/WMTSCapabilities.xml`: return a OGC compatible WMTS document
* `/point/{lon},{lat}`: return a pixel value for the input dataset

### TilerFactory

* `/metadata`: return dataset statistics

##### Optional

* `/preview[.{format}]`: return a preview from the input dataset
* `/crop/{minx},{miny},{maxx},{maxy}.{format}`: return a part of the input dataset

### MosaicTilerFactory

##### Optional

* `/` (POST): Create and Write a MosaicJSON document
* `/` (PUT): Update a MosaicJSON document


## Readers

**Factories** are built on top of [`rio_tiler.io.BaseReader`](https://cogeotiff.github.io/rio-tiler/advanced/custom_readers/), which define basics method to access to a dataset.
