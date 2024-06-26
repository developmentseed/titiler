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
    buffer: Annotated[Optional[float], Query(PydanticUndefined)] = None
) -> Optional[float]
```

Tile buffer Parameter.

    
### ColorFormulaParams

```python3
def ColorFormulaParams(
    color_formula: Annotated[Optional[str], Query(PydanticUndefined)] = None
) -> Optional[str]
```

ColorFormula Parameter.

    
### ColorMapParams

```python3
def ColorMapParams(
    colormap_name: Annotated[Literal['flag_r', 'gist_earth_r', 'cool', 'rdpu_r', 'matter_r', 'tempo_r', 'brbg', 'bwr_r', 'wistia', 'gist_yarg', 'ylgn', 'tarn_r', 'puor', 'purd', 'bupu', 'viridis_r', 'rdylbu_r', 'thermal_r', 'purples_r', 'gnuplot', 'winter', 'twilight_shifted_r', 'gnuplot_r', 'prism', 'viridis', 'pubugn_r', 'oxy', 'haline', 'ylorbr', 'winter_r', 'solar', 'gist_heat', 'rdylbu', 'dark2', 'dark2_r', 'terrain_r', 'set3', 'gray_r', 'tab20_r', 'brbg_r', 'rdylgn', 'twilight', 'balance_r', 'summer', 'hot', 'turbid', 'diff', 'speed', 'cmrmap', 'set3_r', 'pastel1', 'piyg_r', 'deep', 'greens_r', 'inferno_r', 'curl_r', 'pubugn', 'seismic_r', 'cmrmap_r', 'hsv_r', 'ylorrd', 'dense', 'oxy_r', 'bwr', 'bone', 'set1_r', 'pastel2', 'reds', 'delta_r', 'gist_rainbow_r', 'orrd_r', 'phase_r', 'pink', 'rainbow_r', 'set2_r', 'bugn', 'ocean', 'copper', 'gist_ncar', 'cubehelix', 'spring_r', 'cool_r', 'ocean_r', 'thermal', 'tab10_r', 'cividis', 'nipy_spectral', 'copper_r', 'inferno', 'amp_r', 'speed_r', 'tab10', 'gist_earth', 'prism_r', 'rdylgn_r', 'twilight_shifted', 'pubu', 'prgn_r', 'gist_gray', 'gray', 'pubu_r', 'purd_r', 'jet', 'flag', 'ice_r', 'tab20c_r', 'paired_r', 'cividis_r', 'gnbu_r', 'autumn_r', 'cfastie', 'spring', 'magma_r', 'rain_r', 'bugn_r', 'afmhot', 'pastel2_r', 'brg_r', 'puor_r', 'nipy_spectral_r', 'gist_stern', 'phase', 'deep_r', 'tempo', 'gist_ncar_r', 'amp', 'balance', 'spectral', 'cubehelix_r', 'delta', 'rain', 'diff_r', 'magma', 'greens', 'reds_r', 'gist_heat_r', 'piyg', 'set1', 'topo_r', 'bone_r', 'binary_r', 'tab20c', 'rdgy_r', 'wistia_r', 'topo', 'algae_r', 'autumn', 'gist_yarg_r', 'ylorrd_r', 'rdbu_r', 'pink_r', 'paired', 'matter', 'terrain', 'twilight_r', 'oranges', 'brg', 'ylgnbu_r', 'purples', 'set2', 'plasma', 'ylorbr_r', 'spectral_r', 'plasma_r', 'coolwarm', 'turbo_r', 'binary', 'schwarzwald', 'rdpu', 'greys_r', 'coolwarm_r', 'tarn', 'algae', 'oranges_r', 'rainbow', 'orrd', 'curl', 'accent', 'rplumbo', 'afmhot_r', 'turbo', 'hsv', 'ylgn_r', 'blues', 'tab20b', 'accent_r', 'ice', 'gist_stern_r', 'blues_r', 'rdbu', 'hot_r', 'jet_r', 'seismic', 'summer_r', 'ylgnbu', 'tab20b_r', 'pastel1_r', 'rdgy', 'gist_rainbow', 'dense_r', 'turbid_r', 'bupu_r', 'solar_r', 'gnbu', 'prgn', 'greys', 'tab20', 'haline_r', 'gist_gray_r', 'gnuplot2_r', 'gnuplot2'], Query(PydanticUndefined)] = None,
    colormap: Annotated[Optional[str], Query(PydanticUndefined)] = None
)
```

    
### CoordCRSParams

```python3
def CoordCRSParams(
    crs: Annotated[Optional[str], Query(PydanticUndefined)] = None
) -> Optional[rasterio.crs.CRS]
```

Coordinate Reference System Coordinates Param.

    
### DatasetPathParams

```python3
def DatasetPathParams(
    url: typing.Annotated[str, Query(PydanticUndefined)]
) -> str
```

Create dataset path from args

    
### DstCRSParams

```python3
def DstCRSParams(
    crs: Annotated[Optional[str], Query(PydanticUndefined)] = None
) -> Optional[rasterio.crs.CRS]
```

Coordinate Reference System Coordinates Param.

    
### RescalingParams

```python3
def RescalingParams(
    rescale: Annotated[Optional[List[str]], Query(PydanticUndefined)] = None
) -> Optional[List[Tuple[float, ...]]]
```

Min/Max data Rescaling

    
### create_colormap_dependency

```python3
def create_colormap_dependency(
    cmap: rio_tiler.colormap.ColorMaps
) -> Callable
```

Create Colormap Dependency.

    
### parse_asset_expression

```python3
def parse_asset_expression(
    asset_expression: Union[Sequence[str], Dict[str, str]]
) -> Dict[str, str]
```

parse asset expression parameters.

    
### parse_asset_indexes

```python3
def parse_asset_indexes(
    asset_indexes: Union[Sequence[str], Dict[str, Sequence[int]]]
) -> Dict[str, Sequence[int]]
```

parse asset indexes parameters.

## Classes

### AssetsBidxExprParams

```python3
class AssetsBidxExprParams(
    indexes: Annotated[Optional[List[int]], Query(PydanticUndefined)] = None,
    assets: Annotated[Optional[List[str]], Query(PydanticUndefined)] = None,
    expression: Annotated[Optional[str], Query(PydanticUndefined)] = None,
    asset_indexes: Annotated[Optional[Sequence[str]], Query(PydanticUndefined)] = None,
    asset_as_band: Annotated[Optional[bool], Query(PydanticUndefined)] = None
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
    indexes: Annotated[Optional[List[int]], Query(PydanticUndefined)] = None,
    assets: Annotated[Optional[List[str]], Query(PydanticUndefined)] = None,
    expression: Annotated[Optional[str], Query(PydanticUndefined)] = None,
    asset_indexes: Annotated[Optional[Sequence[str]], Query(PydanticUndefined)] = None,
    asset_as_band: Annotated[Optional[bool], Query(PydanticUndefined)] = None
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
    indexes: Annotated[Optional[List[int]], Query(PydanticUndefined)] = None,
    assets: Annotated[Optional[List[str]], Query(PydanticUndefined)] = None,
    asset_indexes: Annotated[Optional[Sequence[str]], Query(PydanticUndefined)] = None,
    asset_expression: Annotated[Optional[Sequence[str]], Query(PydanticUndefined)] = None
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
    assets: Annotated[Optional[List[str]], Query(PydanticUndefined)] = None
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
    bands: Annotated[Optional[List[str]], Query(PydanticUndefined)] = None,
    expression: Annotated[Optional[str], Query(PydanticUndefined)] = None
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
    bands: Annotated[Optional[List[str]], Query(PydanticUndefined)] = None,
    expression: Annotated[Optional[str], Query(PydanticUndefined)] = None
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
    bands: Annotated[Optional[List[str]], Query(PydanticUndefined)] = None
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
    indexes: Annotated[Optional[List[int]], Query(PydanticUndefined)] = None,
    expression: Annotated[Optional[str], Query(PydanticUndefined)] = None
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
    indexes: Annotated[Optional[List[int]], Query(PydanticUndefined)] = None
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
    nodata: Annotated[Union[str, int, float, NoneType], Query(PydanticUndefined)] = None,
    unscale: typing.Annotated[bool, Query(PydanticUndefined)] = False,
    resampling_method: Annotated[Literal['nearest', 'bilinear', 'cubic', 'cubic_spline', 'lanczos', 'average', 'mode', 'gauss', 'rms'], Query(PydanticUndefined)] = 'nearest',
    reproject_method: Annotated[Literal['nearest', 'bilinear', 'cubic', 'cubic_spline', 'lanczos', 'average', 'mode', 'sum', 'rms'], Query(PydanticUndefined)] = 'nearest'
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
    expression: Annotated[Optional[str], Query(PydanticUndefined)] = None
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
    bins: Annotated[Optional[str], Query(PydanticUndefined)] = None,
    range: Annotated[Optional[str], Query(PydanticUndefined)] = None
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
    add_mask: typing.Annotated[bool, Query(PydanticUndefined)] = True
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
    max_size: Annotated[Optional[int], 'Maximum image size to read onto.'] = None,
    height: Annotated[Optional[int], 'Force output image height.'] = None,
    width: Annotated[Optional[int], 'Force output image width.'] = None
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
    max_size: typing.Annotated[int, 'Maximum image size to read onto.'] = 1024,
    height: Annotated[Optional[int], 'Force output image height.'] = None,
    width: Annotated[Optional[int], 'Force output image width.'] = None
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
    categorical: typing.Annotated[bool, Query(PydanticUndefined)] = False,
    categories: Annotated[Optional[List[Union[float, int]]], Query(PydanticUndefined)] = None,
    percentiles: Annotated[Optional[List[int]], Query(PydanticUndefined)] = None
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
    buffer: Annotated[Optional[float], Query(PydanticUndefined)] = None,
    padding: Annotated[Optional[int], Query(PydanticUndefined)] = None
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