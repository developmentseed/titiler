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
