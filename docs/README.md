

# Documentations

## Routes

- [Cloud Optimized GeoTIFF](COG.md) - `https://myendpoint/cog/*`
- [SpatioTemporal Asset Catalog](STAC.md) - `https://myendpoint/stac/*`
- [TileMatrixSets](TMS.md) - `https://myendpoint/tileMatrixSets*`

## Customization 

### Color Maps

You can add and register custom colormaps in [`../titiler/custom/cmap.py`](../titiler/custom/cmap.py).

e.g
```python
# colors from https://daac.ornl.gov/ABOVE/guides/Annual_Landcover_ABoVE.html
above_cmap = {
    1: [58, 102, 24, 255],  # Evergreen Forest
    2: [100, 177, 41, 255],  # Deciduous Forest
    3: [177, 177, 41, 255],  # Shrubland
    4: [221, 203, 154, 255],  # Herbaceous
    5: [218, 203, 47, 255],  # Sparely Vegetated
    6: [177, 177, 177, 255],  # Barren
    7: [175, 255, 205, 255],  # Fen
    8: [239, 255, 192, 255],  # Bog
    9: [144, 255, 255, 255],  # Shallows/Littoral
    10: [29, 0, 250, 255],  # Water
}
```

Colormap MUST be dictionaries in form of `Dict[int, Tuple[int, int, int, int]]` as supported by GDAL. Dictionary keys MUST be between 0 and 256.

To make the custom cmap available in the App, you MUST register it in the dependencies [`/titiler/api/deps.py`](../titiler/api/deps.py).

```python
from titiler.custom import cmap as custom_colormap  # Import Custom Colormap submodule
from rio_tiler.colormap import cmap  # Import rio-tiler colormap handler

cmap.register("above", custom_colormap.above_cmap)  # Register the `above` colormap defined earlier
```

### TileMatrixSets

You can add and register custom TileMatrixSets in [`../titiler/custom/tms.py`](../titiler/custom/tms.py). 
TileMatrixSet MUST be defined as morecantile.TileMatrixSet object.

e.g
```python
import morecantile
from rasterio.crs import CRS

# CUSTOM TMS for EPSG:3413
extent = (-4194300, -4194300, 4194300, 4194300)
crs = CRS.from_epsg(3413)
EPSG3413 = morecantile.TileMatrixSet.custom(
    extent, crs, identifier="EPSG3413", matrix_scale=[2, 2]
)
```

To make the custom TMS available in the App, you MUST register it in the dependencies [`/titiler/api/deps.py`](../titiler/api/deps.py).


```python
from titiler.custom import tms as custom_tms
import morecantile

morecantile.tms.register(custom_tms.EPSG3413)
```

### Create Your own app

Titiler can be imported in your python project and you can create your own application from it.

see [Custom_application.md](Custom_application.md) for more.
