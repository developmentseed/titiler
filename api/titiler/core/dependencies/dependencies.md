# Module titiler.core.dependencies

Common dependency.

## Variables

```python3
RescaleType
```

## Functions

    
### BufferParams

```python3
def BufferParams(
    buffer: typing_extensions.Annotated[Union[float, NoneType], Query(PydanticUndefined)] = None
) -> Union[float, NoneType]
```

Tile buffer Parameter.

    
### ColorFormulaParams

```python3
def ColorFormulaParams(
    color_formula: typing_extensions.Annotated[Union[str, NoneType], Query(PydanticUndefined)] = None
) -> Union[str, NoneType]
```

ColorFormula Parameter.

    
### ColorMapParams

```python3
def ColorMapParams(
    colormap_name: typing_extensions.Annotated[Literal['rdbu', 'turbid_r', 'bone_r', 'orrd_r', 'tempo', 'pubu', 'summer', 'gist_gray', 'cmrmap_r', 'rdgy', 'greens', 'hsv_r', 'gnuplot_r', 'nipy_spectral_r', 'purd', 'accent_r', 'paired', 'spring', 'tab20_r', 'speed', 'oxy_r', 'plasma_r', 'tarn', 'terrain_r', 'inferno', 'ylgn', 'ice_r', 'tab20b_r', 'prism_r', 'diff', 'twilight_r', 'afmhot_r', 'oranges', 'speed_r', 'delta_r', 'deep_r', 'spectral_r', 'gnbu', 'thermal_r', 'jet', 'rplumbo', 'gist_earth', 'ice', 'gist_gray_r', 'set1_r', 'rainbow_r', 'brbg', 'turbo_r', 'orrd', 'solar', 'pastel1', 'reds_r', 'balance_r', 'piyg_r', 'rain_r', 'pubugn_r', 'ocean', 'algae_r', 'magma', 'tempo_r', 'rdpu', 'brg', 'bone', 'jet_r', 'binary_r', 'pink', 'rdylgn', 'piyg', 'turbo', 'dark2_r', 'algae', 'gray', 'hot', 'ylgn_r', 'paired_r', 'set3', 'ylorbr_r', 'brg_r', 'pubugn', 'blues_r', 'rdylbu', 'pubu_r', 'nipy_spectral', 'matter', 'tab20b', 'bupu_r', 'haline_r', 'tab20c', 'ylgnbu', 'bugn', 'solar_r', 'delta', 'cmrmap', 'binary', 'autumn_r', 'coolwarm', 'autumn', 'bupu', 'gnbu_r', 'pastel1_r', 'copper', 'wistia_r', 'tab20c_r', 'seismic', 'gist_stern_r', 'tab10', 'copper_r', 'accent', 'cividis_r', 'gist_ncar', 'gist_ncar_r', 'ylorbr', 'topo', 'balance', 'winter_r', 'gist_heat_r', 'ylgnbu_r', 'brbg_r', 'dense_r', 'gray_r', 'rdylbu_r', 'set2', 'gist_yarg', 'inferno_r', 'cool_r', 'prgn', 'gist_stern', 'pink_r', 'blues', 'greys_r', 'terrain', 'oranges_r', 'cubehelix', 'pastel2', 'greys', 'spectral', 'gist_heat', 'ylorrd', 'tarn_r', 'gist_rainbow', 'prism', 'greens_r', 'rain', 'hot_r', 'winter', 'amp', 'gnuplot', 'deep', 'ylorrd_r', 'amp_r', 'rdylgn_r', 'twilight_shifted', 'oxy', 'gist_earth_r', 'puor_r', 'twilight', 'purd_r', 'puor', 'thermal', 'haline', 'wistia', 'purples_r', 'rdgy_r', 'gist_rainbow_r', 'gnuplot2', 'viridis_r', 'ocean_r', 'set1', 'gist_yarg_r', 'dense', 'rdbu_r', 'flag', 'set3_r', 'plasma', 'twilight_shifted_r', 'turbid', 'phase_r', 'matter_r', 'bwr_r', 'tab10_r', 'diff_r', 'bwr', 'curl', 'afmhot', 'schwarzwald', 'reds', 'topo_r', 'magma_r', 'set2_r', 'pastel2_r', 'dark2', 'hsv', 'phase', 'spring_r', 'flag_r', 'coolwarm_r', 'cubehelix_r', 'cividis', 'purples', 'cool', 'gnuplot2_r', 'seismic_r', 'summer_r', 'prgn_r', 'cfastie', 'curl_r', 'viridis', 'bugn_r', 'rdpu_r', 'rainbow', 'tab20'], Query(PydanticUndefined)] = None,
    colormap: typing_extensions.Annotated[Union[str, NoneType], Query(PydanticUndefined)] = None
)
```

    
### CoordCRSParams

```python3
def CoordCRSParams(
    crs: typing_extensions.Annotated[Union[str, NoneType], Query(PydanticUndefined)] = None
) -> Union[rasterio.crs.CRS, NoneType]
```

Coordinate Reference System Coordinates Param.

    
### DatasetPathParams

```python3
def DatasetPathParams(
    url: typing_extensions.Annotated[str, Query(PydanticUndefined)]
) -> str
```

Create dataset path from args

    
### DstCRSParams

```python3
def DstCRSParams(
    crs: typing_extensions.Annotated[Union[str, NoneType], Query(PydanticUndefined)] = None
) -> Union[rasterio.crs.CRS, NoneType]
```

Coordinate Reference System Coordinates Param.

    
### RescalingParams

```python3
def RescalingParams(
    rescale: typing_extensions.Annotated[Union[List[str], NoneType], Query(PydanticUndefined)] = None
) -> Union[List[Tuple[float, ...]], NoneType]
```

Min/Max data Rescaling

    
### create_colormap_dependency

```python3
def create_colormap_dependency(
    cmap: rio_tiler.colormap.ColorMaps
) -> Callable
```

Create Colormap Dependency.

## Classes

### AssetsBidxExprParams

```python3
class AssetsBidxExprParams(
    indexes: typing_extensions.Annotated[Union[List[int], NoneType], Query(PydanticUndefined)] = None,
    assets: typing_extensions.Annotated[Union[List[str], NoneType], Query(PydanticUndefined)] = None,
    expression: typing_extensions.Annotated[Union[str, NoneType], Query(PydanticUndefined)] = None,
    asset_indexes: typing_extensions.Annotated[Union[Sequence[str], NoneType], Query(PydanticUndefined)] = None,
    asset_as_band: typing_extensions.Annotated[Union[bool, NoneType], Query(PydanticUndefined)] = None
)
```

Assets, Expression and Asset's band Indexes parameters.

#### Ancestors (in MRO)

* titiler.core.dependencies.AssetsParams
* titiler.core.dependencies.BidxParams
* titiler.core.dependencies.DefaultDependency

#### Descendants

* titiler.core.dependencies.AssetsBidxExprParamsOptional

#### Class variables

```python3
asset_as_band
```

```python3
asset_indexes
```

```python3
assets
```

```python3
expression
```

```python3
indexes
```

#### Methods

    
#### keys

```python3
def keys(
    self
)
```

Return Keys.

### AssetsBidxExprParamsOptional

```python3
class AssetsBidxExprParamsOptional(
    indexes: typing_extensions.Annotated[Union[List[int], NoneType], Query(PydanticUndefined)] = None,
    assets: typing_extensions.Annotated[Union[List[str], NoneType], Query(PydanticUndefined)] = None,
    expression: typing_extensions.Annotated[Union[str, NoneType], Query(PydanticUndefined)] = None,
    asset_indexes: typing_extensions.Annotated[Union[Sequence[str], NoneType], Query(PydanticUndefined)] = None,
    asset_as_band: typing_extensions.Annotated[Union[bool, NoneType], Query(PydanticUndefined)] = None
)
```

Assets, Expression and Asset's band Indexes parameters but with no requirement.

#### Ancestors (in MRO)

* titiler.core.dependencies.AssetsBidxExprParams
* titiler.core.dependencies.AssetsParams
* titiler.core.dependencies.BidxParams
* titiler.core.dependencies.DefaultDependency

#### Class variables

```python3
asset_as_band
```

```python3
asset_indexes
```

```python3
assets
```

```python3
expression
```

```python3
indexes
```

#### Methods

    
#### keys

```python3
def keys(
    self
)
```

Return Keys.

### AssetsBidxParams

```python3
class AssetsBidxParams(
    indexes: typing_extensions.Annotated[Union[List[int], NoneType], Query(PydanticUndefined)] = None,
    assets: typing_extensions.Annotated[Union[List[str], NoneType], Query(PydanticUndefined)] = None,
    asset_indexes: typing_extensions.Annotated[Union[Sequence[str], NoneType], Query(PydanticUndefined)] = None,
    asset_expression: typing_extensions.Annotated[Union[Sequence[str], NoneType], Query(PydanticUndefined)] = None
)
```

Assets, Asset's band Indexes and Asset's band Expression parameters.

#### Ancestors (in MRO)

* titiler.core.dependencies.AssetsParams
* titiler.core.dependencies.BidxParams
* titiler.core.dependencies.DefaultDependency

#### Class variables

```python3
asset_expression
```

```python3
asset_indexes
```

```python3
assets
```

```python3
indexes
```

#### Methods

    
#### keys

```python3
def keys(
    self
)
```

Return Keys.

### AssetsParams

```python3
class AssetsParams(
    assets: typing_extensions.Annotated[Union[List[str], NoneType], Query(PydanticUndefined)] = None
)
```

Assets parameters.

#### Ancestors (in MRO)

* titiler.core.dependencies.DefaultDependency

#### Descendants

* titiler.core.dependencies.AssetsBidxExprParams
* titiler.core.dependencies.AssetsBidxParams

#### Class variables

```python3
assets
```

#### Methods

    
#### keys

```python3
def keys(
    self
)
```

Return Keys.

### BandsExprParams

```python3
class BandsExprParams(
    bands: typing_extensions.Annotated[Union[List[str], NoneType], Query(PydanticUndefined)] = None,
    expression: typing_extensions.Annotated[Union[str, NoneType], Query(PydanticUndefined)] = None
)
```

Band names and Expression parameters (Band or Expression required).

#### Ancestors (in MRO)

* titiler.core.dependencies.ExpressionParams
* titiler.core.dependencies.BandsParams
* titiler.core.dependencies.DefaultDependency

#### Class variables

```python3
bands
```

```python3
expression
```

#### Methods

    
#### keys

```python3
def keys(
    self
)
```

Return Keys.

### BandsExprParamsOptional

```python3
class BandsExprParamsOptional(
    bands: typing_extensions.Annotated[Union[List[str], NoneType], Query(PydanticUndefined)] = None,
    expression: typing_extensions.Annotated[Union[str, NoneType], Query(PydanticUndefined)] = None
)
```

Optional Band names and Expression parameters.

#### Ancestors (in MRO)

* titiler.core.dependencies.ExpressionParams
* titiler.core.dependencies.BandsParams
* titiler.core.dependencies.DefaultDependency

#### Class variables

```python3
bands
```

```python3
expression
```

#### Methods

    
#### keys

```python3
def keys(
    self
)
```

Return Keys.

### BandsParams

```python3
class BandsParams(
    bands: typing_extensions.Annotated[Union[List[str], NoneType], Query(PydanticUndefined)] = None
)
```

Band names parameters.

#### Ancestors (in MRO)

* titiler.core.dependencies.DefaultDependency

#### Descendants

* titiler.core.dependencies.BandsExprParamsOptional
* titiler.core.dependencies.BandsExprParams

#### Class variables

```python3
bands
```

#### Methods

    
#### keys

```python3
def keys(
    self
)
```

Return Keys.

### BidxExprParams

```python3
class BidxExprParams(
    indexes: typing_extensions.Annotated[Union[List[int], NoneType], Query(PydanticUndefined)] = None,
    expression: typing_extensions.Annotated[Union[str, NoneType], Query(PydanticUndefined)] = None
)
```

Band Indexes and Expression parameters.

#### Ancestors (in MRO)

* titiler.core.dependencies.ExpressionParams
* titiler.core.dependencies.BidxParams
* titiler.core.dependencies.DefaultDependency

#### Class variables

```python3
expression
```

```python3
indexes
```

#### Methods

    
#### keys

```python3
def keys(
    self
)
```

Return Keys.

### BidxParams

```python3
class BidxParams(
    indexes: typing_extensions.Annotated[Union[List[int], NoneType], Query(PydanticUndefined)] = None
)
```

Band Indexes parameters.

#### Ancestors (in MRO)

* titiler.core.dependencies.DefaultDependency

#### Descendants

* titiler.core.dependencies.BidxExprParams
* titiler.core.dependencies.AssetsBidxExprParams
* titiler.core.dependencies.AssetsBidxParams

#### Class variables

```python3
indexes
```

#### Methods

    
#### keys

```python3
def keys(
    self
)
```

Return Keys.

### DatasetParams

```python3
class DatasetParams(
    nodata: typing_extensions.Annotated[Union[str, int, float, NoneType], Query(PydanticUndefined)] = None,
    unscale: typing_extensions.Annotated[bool, Query(PydanticUndefined)] = False,
    resampling_method: typing_extensions.Annotated[Literal['nearest', 'bilinear', 'cubic', 'cubic_spline', 'lanczos', 'average', 'mode', 'gauss', 'rms'], Query(PydanticUndefined)] = 'nearest',
    reproject_method: typing_extensions.Annotated[Literal['nearest', 'bilinear', 'cubic', 'cubic_spline', 'lanczos', 'average', 'mode', 'sum', 'rms'], Query(PydanticUndefined)] = 'nearest'
)
```

Low level WarpedVRT Optional parameters.

#### Ancestors (in MRO)

* titiler.core.dependencies.DefaultDependency

#### Class variables

```python3
nodata
```

```python3
reproject_method
```

```python3
resampling_method
```

```python3
unscale
```

#### Methods

    
#### keys

```python3
def keys(
    self
)
```

Return Keys.

### DefaultDependency

```python3
class DefaultDependency(
    
)
```

Dataclass with dict unpacking

#### Descendants

* titiler.core.dependencies.BidxParams
* titiler.core.dependencies.ExpressionParams
* titiler.core.dependencies.AssetsParams
* titiler.core.dependencies.BandsParams
* titiler.core.dependencies.PreviewParams
* titiler.core.dependencies.PartFeatureParams
* titiler.core.dependencies.DatasetParams
* titiler.core.dependencies.ImageRenderingParams
* titiler.core.dependencies.StatisticsParams
* titiler.core.dependencies.HistogramParams
* titiler.core.dependencies.TileParams

#### Methods

    
#### keys

```python3
def keys(
    self
)
```

Return Keys.

### ExpressionParams

```python3
class ExpressionParams(
    expression: typing_extensions.Annotated[Union[str, NoneType], Query(PydanticUndefined)] = None
)
```

Expression parameters.

#### Ancestors (in MRO)

* titiler.core.dependencies.DefaultDependency

#### Descendants

* titiler.core.dependencies.BidxExprParams
* titiler.core.dependencies.BandsExprParamsOptional
* titiler.core.dependencies.BandsExprParams

#### Class variables

```python3
expression
```

#### Methods

    
#### keys

```python3
def keys(
    self
)
```

Return Keys.

### HistogramParams

```python3
class HistogramParams(
    bins: typing_extensions.Annotated[Union[str, NoneType], Query(PydanticUndefined)] = None,
    range: typing_extensions.Annotated[Union[str, NoneType], Query(PydanticUndefined)] = None
)
```

Numpy Histogram options.

#### Ancestors (in MRO)

* titiler.core.dependencies.DefaultDependency

#### Class variables

```python3
bins
```

```python3
range
```

#### Methods

    
#### keys

```python3
def keys(
    self
)
```

Return Keys.

### ImageRenderingParams

```python3
class ImageRenderingParams(
    add_mask: typing_extensions.Annotated[bool, Query(PydanticUndefined)] = True
)
```

Image Rendering options.

#### Ancestors (in MRO)

* titiler.core.dependencies.DefaultDependency

#### Class variables

```python3
add_mask
```

#### Methods

    
#### keys

```python3
def keys(
    self
)
```

Return Keys.

### PartFeatureParams

```python3
class PartFeatureParams(
    max_size: typing_extensions.Annotated[Union[int, NoneType], 'Maximum image size to read onto.'] = None,
    height: typing_extensions.Annotated[Union[int, NoneType], 'Force output image height.'] = None,
    width: typing_extensions.Annotated[Union[int, NoneType], 'Force output image width.'] = None
)
```

Common parameters for bbox and feature.

#### Ancestors (in MRO)

* titiler.core.dependencies.DefaultDependency

#### Class variables

```python3
height
```

```python3
max_size
```

```python3
width
```

#### Methods

    
#### keys

```python3
def keys(
    self
)
```

Return Keys.

### PreviewParams

```python3
class PreviewParams(
    max_size: typing_extensions.Annotated[int, 'Maximum image size to read onto.'] = 1024,
    height: typing_extensions.Annotated[Union[int, NoneType], 'Force output image height.'] = None,
    width: typing_extensions.Annotated[Union[int, NoneType], 'Force output image width.'] = None
)
```

Common Preview parameters.

#### Ancestors (in MRO)

* titiler.core.dependencies.DefaultDependency

#### Class variables

```python3
height
```

```python3
max_size
```

```python3
width
```

#### Methods

    
#### keys

```python3
def keys(
    self
)
```

Return Keys.

### StatisticsParams

```python3
class StatisticsParams(
    categorical: typing_extensions.Annotated[bool, Query(PydanticUndefined)] = False,
    categories: typing_extensions.Annotated[Union[List[Union[float, int]], NoneType], Query(PydanticUndefined)] = None,
    percentiles: typing_extensions.Annotated[Union[List[int], NoneType], Query(PydanticUndefined)] = None
)
```

Statistics options.

#### Ancestors (in MRO)

* titiler.core.dependencies.DefaultDependency

#### Class variables

```python3
categorical
```

```python3
categories
```

```python3
percentiles
```

#### Methods

    
#### keys

```python3
def keys(
    self
)
```

Return Keys.

### TileParams

```python3
class TileParams(
    buffer: typing_extensions.Annotated[Union[float, NoneType], Query(PydanticUndefined)] = None,
    padding: typing_extensions.Annotated[Union[int, NoneType], Query(PydanticUndefined)] = None
)
```

Tile options.

#### Ancestors (in MRO)

* titiler.core.dependencies.DefaultDependency

#### Class variables

```python3
buffer
```

```python3
padding
```

#### Methods

    
#### keys

```python3
def keys(
    self
)
```

Return Keys.