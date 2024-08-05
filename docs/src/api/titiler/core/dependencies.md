# Module titiler.core.dependencies

Common dependency.

None

## Functions

    
### ColorMapParams

```python3
def ColorMapParams(
    colormap_name: titiler.core.dependencies.ColorMapName = Query(None),
    colormap: str = Query(None)
) -> Union[Dict, Sequence, NoneType]
```

    
Colormap Dependency.

    
### DatasetPathParams

```python3
def DatasetPathParams(
    url: str = Query(Ellipsis)
) -> str
```

    
Create dataset path from args

    
### TMSParams

```python3
def TMSParams(
    TileMatrixSetId: titiler.core.dependencies.TileMatrixSetName = Query(TileMatrixSetName.WebMercatorQuad)
) -> morecantile.models.TileMatrixSet
```

    
TileMatrixSet Dependency.

    
### WebMercatorTMSParams

```python3
def WebMercatorTMSParams(
    TileMatrixSetId: titiler.core.dependencies.WebMercatorTileMatrixSetName = Query(WebMercatorTileMatrixSetName.WebMercatorQuad)
) -> morecantile.models.TileMatrixSet
```

    
TileMatrixSet Dependency.

## Classes

### AssetsBidxExprParams

```python3
class AssetsBidxExprParams(
    assets: Union[List[str], NoneType] = Query(None),
    expression: Union[str, NoneType] = Query(None),
    asset_indexes: Union[Sequence[str], NoneType] = Query(None),
    asset_expression: Union[Sequence[str], NoneType] = Query(None)
)
```

#### Ancestors (in MRO)

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

### AssetsBidxParams

```python3
class AssetsBidxParams(
    assets: List[str] = Query(None),
    asset_indexes: Union[Sequence[str], NoneType] = Query(None),
    asset_expression: Union[Sequence[str], NoneType] = Query(None)
)
```

#### Ancestors (in MRO)

* titiler.core.dependencies.AssetsParams
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
    assets: List[str] = Query(None)
)
```

#### Ancestors (in MRO)

* titiler.core.dependencies.DefaultDependency

#### Descendants

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
    bands: List[str] = Query(None),
    expression: Union[str, NoneType] = Query(None)
)
```

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
    bands: List[str] = Query(None),
    expression: Union[str, NoneType] = Query(None)
)
```

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
    bands: List[str] = Query(None)
)
```

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
    indexes: Union[List[int], NoneType] = Query(None),
    expression: Union[str, NoneType] = Query(None)
)
```

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
    indexes: Union[List[int], NoneType] = Query(None)
)
```

#### Ancestors (in MRO)

* titiler.core.dependencies.DefaultDependency

#### Descendants

* titiler.core.dependencies.BidxExprParams

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

### ColorMapName

```python3
class ColorMapName(
    /,
    *args,
    **kwargs
)
```

#### Ancestors (in MRO)

* enum.Enum

#### Class variables

```python3
accent
```

```python3
accent_r
```

```python3
afmhot
```

```python3
afmhot_r
```

```python3
autumn
```

```python3
autumn_r
```

```python3
binary
```

```python3
binary_r
```

```python3
blues
```

```python3
blues_r
```

```python3
bone
```

```python3
bone_r
```

```python3
brbg
```

```python3
brbg_r
```

```python3
brg
```

```python3
brg_r
```

```python3
bugn
```

```python3
bugn_r
```

```python3
bupu
```

```python3
bupu_r
```

```python3
bwr
```

```python3
bwr_r
```

```python3
cfastie
```

```python3
cividis
```

```python3
cividis_r
```

```python3
cmrmap
```

```python3
cmrmap_r
```

```python3
cool
```

```python3
cool_r
```

```python3
coolwarm
```

```python3
coolwarm_r
```

```python3
copper
```

```python3
copper_r
```

```python3
cubehelix
```

```python3
cubehelix_r
```

```python3
dark2
```

```python3
dark2_r
```

```python3
flag
```

```python3
flag_r
```

```python3
gist_earth
```

```python3
gist_earth_r
```

```python3
gist_gray
```

```python3
gist_gray_r
```

```python3
gist_heat
```

```python3
gist_heat_r
```

```python3
gist_ncar
```

```python3
gist_ncar_r
```

```python3
gist_rainbow
```

```python3
gist_rainbow_r
```

```python3
gist_stern
```

```python3
gist_stern_r
```

```python3
gist_yarg
```

```python3
gist_yarg_r
```

```python3
gnbu
```

```python3
gnbu_r
```

```python3
gnuplot
```

```python3
gnuplot2
```

```python3
gnuplot2_r
```

```python3
gnuplot_r
```

```python3
gray
```

```python3
gray_r
```

```python3
greens
```

```python3
greens_r
```

```python3
greys
```

```python3
greys_r
```

```python3
hot
```

```python3
hot_r
```

```python3
hsv
```

```python3
hsv_r
```

```python3
inferno
```

```python3
inferno_r
```

```python3
jet
```

```python3
jet_r
```

```python3
magma
```

```python3
magma_r
```

```python3
name
```

```python3
nipy_spectral
```

```python3
nipy_spectral_r
```

```python3
ocean
```

```python3
ocean_r
```

```python3
oranges
```

```python3
oranges_r
```

```python3
orrd
```

```python3
orrd_r
```

```python3
paired
```

```python3
paired_r
```

```python3
pastel1
```

```python3
pastel1_r
```

```python3
pastel2
```

```python3
pastel2_r
```

```python3
pink
```

```python3
pink_r
```

```python3
piyg
```

```python3
piyg_r
```

```python3
plasma
```

```python3
plasma_r
```

```python3
prgn
```

```python3
prgn_r
```

```python3
prism
```

```python3
prism_r
```

```python3
pubu
```

```python3
pubu_r
```

```python3
pubugn
```

```python3
pubugn_r
```

```python3
puor
```

```python3
puor_r
```

```python3
purd
```

```python3
purd_r
```

```python3
purples
```

```python3
purples_r
```

```python3
rainbow
```

```python3
rainbow_r
```

```python3
rdbu
```

```python3
rdbu_r
```

```python3
rdgy
```

```python3
rdgy_r
```

```python3
rdpu
```

```python3
rdpu_r
```

```python3
rdylbu
```

```python3
rdylbu_r
```

```python3
rdylgn
```

```python3
rdylgn_r
```

```python3
reds
```

```python3
reds_r
```

```python3
rplumbo
```

```python3
schwarzwald
```

```python3
seismic
```

```python3
seismic_r
```

```python3
set1
```

```python3
set1_r
```

```python3
set2
```

```python3
set2_r
```

```python3
set3
```

```python3
set3_r
```

```python3
spectral
```

```python3
spectral_r
```

```python3
spring
```

```python3
spring_r
```

```python3
summer
```

```python3
summer_r
```

```python3
tab10
```

```python3
tab10_r
```

```python3
tab20
```

```python3
tab20_r
```

```python3
tab20b
```

```python3
tab20b_r
```

```python3
tab20c
```

```python3
tab20c_r
```

```python3
terrain
```

```python3
terrain_r
```

```python3
twilight
```

```python3
twilight_r
```

```python3
twilight_shifted
```

```python3
twilight_shifted_r
```

```python3
value
```

```python3
viridis
```

```python3
viridis_r
```

```python3
winter
```

```python3
winter_r
```

```python3
wistia
```

```python3
wistia_r
```

```python3
ylgn
```

```python3
ylgn_r
```

```python3
ylgnbu
```

```python3
ylgnbu_r
```

```python3
ylorbr
```

```python3
ylorbr_r
```

```python3
ylorrd
```

```python3
ylorrd_r
```

### DatasetParams

```python3
class DatasetParams(
    nodata: Union[str, int, float, NoneType] = Query(None),
    unscale: Union[bool, NoneType] = Query(False),
    resampling_method: titiler.core.dependencies.ResamplingName = Query(ResamplingName.nearest)
)
```

#### Ancestors (in MRO)

* titiler.core.dependencies.DefaultDependency

#### Class variables

```python3
nodata
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

#### Descendants

* titiler.core.dependencies.BidxParams
* titiler.core.dependencies.ExpressionParams
* titiler.core.dependencies.AssetsParams
* titiler.core.dependencies.AssetsBidxExprParams
* titiler.core.dependencies.BandsParams
* titiler.core.dependencies.ImageParams
* titiler.core.dependencies.DatasetParams
* titiler.core.dependencies.ImageRenderingParams
* titiler.core.dependencies.PostProcessParams

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
    expression: Union[str, NoneType] = Query(None)
)
```

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

### ImageParams

```python3
class ImageParams(
    max_size: Union[int, NoneType] = Query(1024),
    height: Union[int, NoneType] = Query(None),
    width: Union[int, NoneType] = Query(None)
)
```

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

### ImageRenderingParams

```python3
class ImageRenderingParams(
    add_mask: bool = Query(True)
)
```

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

### PostProcessParams

```python3
class PostProcessParams(
    in_range: Union[List[str], NoneType] = Query(None),
    color_formula: Union[str, NoneType] = Query(None)
)
```

#### Ancestors (in MRO)

* titiler.core.dependencies.DefaultDependency

#### Class variables

```python3
color_formula
```

```python3
in_range
```

#### Methods

    
#### keys

```python3
def keys(
    self
)
```

    
Return Keys.

### ResamplingName

```python3
class ResamplingName(
    /,
    *args,
    **kwargs
)
```

#### Ancestors (in MRO)

* enum.Enum

#### Class variables

```python3
average
```

```python3
bilinear
```

```python3
cubic
```

```python3
cubic_spline
```

```python3
gauss
```

```python3
lanczos
```

```python3
max
```

```python3
med
```

```python3
min
```

```python3
mode
```

```python3
name
```

```python3
nearest
```

```python3
q1
```

```python3
q3
```

```python3
rms
```

```python3
sum
```

```python3
value
```

### TileMatrixSetName

```python3
class TileMatrixSetName(
    /,
    *args,
    **kwargs
)
```

#### Ancestors (in MRO)

* enum.Enum

#### Class variables

```python3
CanadianNAD83_LCC
```

```python3
EuropeanETRS89_LAEAQuad
```

```python3
LINZAntarticaMapTilegrid
```

```python3
NZTM2000
```

```python3
NZTM2000Quad
```

```python3
UPSAntarcticWGS84Quad
```

```python3
UPSArcticWGS84Quad
```

```python3
UTM31WGS84Quad
```

```python3
WebMercatorQuad
```

```python3
WorldCRS84Quad
```

```python3
WorldMercatorWGS84Quad
```

```python3
name
```

```python3
value
```

### WebMercatorTileMatrixSetName

```python3
class WebMercatorTileMatrixSetName(
    /,
    *args,
    **kwargs
)
```

#### Ancestors (in MRO)

* enum.Enum

#### Class variables

```python3
WebMercatorQuad
```

```python3
name
```

```python3
value
```