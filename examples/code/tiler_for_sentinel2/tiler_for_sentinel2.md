**Goal**: Create a dynamic tiler for Sentinel-2 (using AWS Public Dataset)

**requirements**: titiler.core, titiler.mosaic, rio-tiler-pds

Note: See https://github.com/developmentseed/titiler-pds for a end-to-end implementation

### Sentinel 2

Thanks to Digital Earth Africa and in collaboration with Sinergise, Element 84, Amazon Web Services (AWS) and the Committee on Earth Observation Satellites (CEOS), Sentinel 2 (Level 2) data over Africa, usually stored as JPEG2000, has been translated to COG. More importantly, a STAC database and API has been set up.

https://www.digitalearthafrica.org/news/operational-and-ready-use-satellite-data-now-available-across-africa

The API is provided by [@element84](https://www.element84.com) and follows the latest specification: https://earth-search.aws.element84.com/v0


```python
"""Sentinel 2 (COG) Tiler."""

from titiler.core.factory import MultiBandTilerFactory
from titiler.core.dependencies import BandsExprParams
from titiler.mosaic.factory import MosaicTilerFactory

from rio_tiler_pds.sentinel.aws import S2COGReader
from rio_tiler_pds.sentinel.utils import s2_sceneid_parser

from fastapi import FastAPI, Query


def CustomPathParams(
    sceneid: str = Query(..., description="Sentinel 2 Sceneid.")
):
    """Create dataset path from args"""
    assert s2_sceneid_parser(sceneid)  # Makes sure the sceneid is valid
    return sceneid


app = FastAPI()

scene_tiler = MultiBandTilerFactory(reader=S2COGReader, path_dependency=CustomPathParams, router_prefix="scenes")
app.include_router(scene_tiler.router, prefix="/scenes", tags=["scenes"])

mosaic_tiler = MosaicTilerFactory(
    router_prefix="mosaic",
    dataset_reader=S2COGReader,
    layer_dependency=BandsExprParams,
)
app.include_router(mosaic_tiler.router, prefix="/mosaic", tags=["mosaic"])
```


### How to

1. Search for Data
```python
import os
import json
import base64
import httpx
import datetime
import itertools
import urllib.parse
import pathlib

from io import BytesIO
from functools import partial
from concurrent import futures

from rasterio.plot import reshape_as_image
from rasterio.features import bounds as featureBounds

# Endpoint variables
titiler_endpoint = "http://127.0.0.1:8000"
stac_endpoint = "https://earth-search.aws.element84.com/v0/search"

# Make sure both are up
assert httpx.get(f"{titiler_endpoint}/docs").status_code == 200
assert httpx.get(stac_endpoint).status_code == 200

geojson = {
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {},
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -2.83447265625,
              4.12728532324537
            ],
            [
              2.120361328125,
              4.12728532324537
            ],
            [
              2.120361328125,
              8.254982704877875
            ],
            [
              -2.83447265625,
              8.254982704877875
            ],
            [
              -2.83447265625,
              4.12728532324537
            ]
          ]
        ]
      }
    }
  ]
}

bounds = featureBounds(geojson)

start = datetime.datetime.strptime("2019-01-01", "%Y-%m-%d").strftime("%Y-%m-%dT00:00:00Z")
end = datetime.datetime.strptime("2019-12-11", "%Y-%m-%d").strftime("%Y-%m-%dT23:59:59Z")

# POST body
query = {
    "collections": ["sentinel-s2-l2a-cogs"],
    "datetime": f"{start}/{end}",
    "query": {
        "eo:cloud_cover": {
            "lt": 3
        },
        "sentinel:data_coverage": {
            "gt": 10
        }
    },
    "intersects": geojson["features"][0]["geometry"],
    "limit": 1000,
    "fields": {
      'include': ['id', 'properties.datetime', 'properties.eo:cloud_cover'],  # This will limit the size of returned body
      'exclude': ['assets', 'links']  # This will limit the size of returned body
    },
    "sortby": [
        {
            "field": "properties.eo:cloud_cover",
            "direction": "desc"
        },
    ]
}

# POST Headers
headers = {
    "Content-Type": "application/json",
    "Accept-Encoding": "gzip",
    "Accept": "application/geo+json",
}

data = httpx.post(stac_endpoint, headers=headers, json=query).json()
print("Results context:")
print(data["context"])

sceneid = [f["id"] for f in data["features"]]
cloudcover = [f["properties"]["eo:cloud_cover"] for f in data["features"]]
dates = [f["properties"]["datetime"][0:10] for f in data["features"]]
```

2. Get TileJSON
```python
# Fetch TileJSON
# For this example we use the first `sceneid` returned from the STAC API
# and we sent the Bands to B04,B03,B02 which are red,green,blue
data = httpx.get(f"{titiler_endpoint}/scenes/WebMercatorQuad/tilejson.json?sceneid={sceneid[4]}&bands=B04&bands=B03&bands=B02&rescale=0,2000").json()
print(data)
```

3. Mosaic

```python
from cogeo_mosaic.backends import MosaicBackend
from typing import Dict, List, Sequence, Optional
from pygeos import polygons
import mercantile

# Simple Mosaic
def custom_accessor(feature):
    """Return feature identifier."""
    return feature["id"]

with MosaicBackend(
    "stac+https://earth-search.aws.element84.com/v0/search",
    query,
    minzoom=8,
    maxzoom=15,
    mosaic_options={"accessor": custom_accessor},
) as mosaic:
    print(mosaic.metadata)
    mosaic_doc = mosaic.mosaic_def.dict(exclude_none=True)

# Optimized Mosaic
def optimized_filter(
    tile: mercantile.Tile,  # noqa
    dataset: Sequence[Dict],
    geoms: Sequence[polygons],
    minimum_tile_cover=None,  # noqa
    tile_cover_sort=False,  # noqa
    maximum_items_per_tile: Optional[int] = None,
) -> List:
    """Optimized filter that keeps only one item per grid ID."""
    gridid: List[str] = []
    selected_dataset: List[Dict] = []

    for item in dataset:
        grid = item["id"].split("_")[1]
        if grid not in gridid:
            gridid.append(grid)
            selected_dataset.append(item)

    dataset = selected_dataset

    indices = list(range(len(dataset)))
    if maximum_items_per_tile:
        indices = indices[:maximum_items_per_tile]

    return [dataset[ind] for ind in indices]


with MosaicBackend(
    "stac+https://earth-search.aws.element84.com/v0/search",
    query,
    minzoom=8,
    maxzoom=14,
    mosaic_options={"accessor": custom_accessor, "asset_filter": optimized_filter},
) as mosaic:
    print(mosaic.metadata)
    mosaic_doc = mosa

# Write the mosaic
mosaic_file = "mymosaic.json.gz"
with MosaicBackend(mosaic_file, mosaic_def=mosaic_doc) as mosaic:
    mosaic.write(overwrite=True)
```

Use the mosaic in titiler
```python
mosaic = str(pathlib.Path(mosaic_file).absolute())
data = httpx.get(f"{titiler_endpoint}/mosaic/WebMercatorQuad/tilejson.json?url=file:///{mosaic}&bands=B01&rescale=0,1000").json()
print(data)
```
