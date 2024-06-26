# Module titiler.core.factory

TiTiler Router factories.

## Variables

```python3
DEFAULT_TEMPLATES
```

```python3
WGS84_CRS
```

```python3
img_endpoint_params
```

```python3
jinja2_env
```

## Classes

### AlgorithmFactory

```python3
class AlgorithmFactory(
    supported_algorithm: titiler.core.algorithm.Algorithms = Algorithms(data={'hillshade': <class 'titiler.core.algorithm.dem.HillShade'>, 'contours': <class 'titiler.core.algorithm.dem.Contours'>, 'normalizedIndex': <class 'titiler.core.algorithm.index.NormalizedIndex'>, 'terrarium': <class 'titiler.core.algorithm.dem.Terrarium'>, 'terrainrgb': <class 'titiler.core.algorithm.dem.TerrainRGB'>}),
    router: fastapi.routing.APIRouter = <factory>
)
```

Algorithm endpoints Factory.

#### Class variables

```python3
supported_algorithm
```

### BaseTilerFactory

```python3
class BaseTilerFactory(
    reader: Type[rio_tiler.io.base.BaseReader],
    router: fastapi.routing.APIRouter = <factory>,
    path_dependency: Callable[..., Any] = <function DatasetPathParams at 0x7f1b17ce37e0>,
    layer_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.BidxExprParams'>,
    dataset_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.DatasetParams'>,
    process_dependency: Callable[..., Optional[titiler.core.algorithm.base.BaseAlgorithm]] = <function Algorithms.dependency.<locals>.post_process at 0x7f1b0d806160>,
    rescale_dependency: Callable[..., Optional[List[Tuple[float, ...]]]] = <function RescalingParams at 0x7f1b0db8f880>,
    color_formula_dependency: Callable[..., Optional[str]] = <function ColorFormulaParams at 0x7f1b0dbb6fc0>,
    colormap_dependency: Callable[..., Union[Dict[int, Tuple[int, int, int, int]], Sequence[Tuple[Tuple[Union[float, int], Union[float, int]], Tuple[int, int, int, int]]], NoneType]] = <function create_colormap_dependency.<locals>.deps at 0x7f1b17ce3560>,
    render_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.ImageRenderingParams'>,
    reader_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.DefaultDependency'>,
    environment_dependency: Callable[..., Dict] = <function BaseTilerFactory.<lambda> at 0x7f1b0d806200>,
    supported_tms: morecantile.defaults.TileMatrixSets = TileMatrixSets(tms={'CDB1GlobalGrid': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/CDB1GlobalGrid.json'), 'CanadianNAD83_LCC': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/CanadianNAD83_LCC.json'), 'EuropeanETRS89_LAEAQuad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/EuropeanETRS89_LAEAQuad.json'), 'GNOSISGlobalGrid': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/GNOSISGlobalGrid.json'), 'LINZAntarticaMapTilegrid': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/LINZAntarticaMapTilegrid.json'), 'NZTM2000Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/NZTM2000Quad.json'), 'UPSAntarcticWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/UPSAntarcticWGS84Quad.json'), 'UPSArcticWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/UPSArcticWGS84Quad.json'), 'UTM31WGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/UTM31WGS84Quad.json'), 'WGS1984Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/WGS1984Quad.json'), 'WebMercatorQuad': <TileMatrixSet title='Google Maps Compatible for the World' id='WebMercatorQuad' crs='http://www.opengis.net/def/crs/EPSG/0/3857>, 'WorldCRS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/WorldCRS84Quad.json'), 'WorldMercatorWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/WorldMercatorWGS84Quad.json')}),
    default_tms: Optional[str] = None,
    router_prefix: str = '',
    optional_headers: List[titiler.core.resources.enums.OptionalHeader] = <factory>,
    route_dependencies: List[Tuple[List[titiler.core.routing.EndpointScope], List[fastapi.params.Depends]]] = <factory>,
    extensions: List[titiler.core.factory.FactoryExtension] = <factory>,
    templates: starlette.templating.Jinja2Templates = <starlette.templating.Jinja2Templates object at 0x7f1b0d93cd10>
)
```

BaseTiler Factory.

Abstract Base Class which defines most inputs used by dynamic tiler.
#### Attributes

| Name | Type | Description | Default |
|---|---|---|---|
| reader | rio_tiler.io.base.BaseReader | A rio-tiler reader (e.g Reader). | None |
| router | fastapi.APIRouter | Application router to register endpoints to. | None |
| path_dependency | Callable | Endpoint dependency defining `path` to pass to the reader init. | None |
| dataset_dependency | titiler.core.dependencies.DefaultDependency | Endpoint dependency defining dataset overwriting options (e.g nodata). | None |
| layer_dependency | titiler.core.dependencies.DefaultDependency | Endpoint dependency defining dataset indexes/bands/assets options. | None |
| render_dependency | titiler.core.dependencies.DefaultDependency | Endpoint dependency defining image rendering options (e.g add_mask). | None |
| colormap_dependency | Callable | Endpoint dependency defining ColorMap options (e.g colormap_name). | None |
| process_dependency | titiler.core.dependencies.DefaultDependency | Endpoint dependency defining image post-processing options (e.g rescaling, color-formula). | None |
| tms_dependency | Callable | Endpoint dependency defining TileMatrixSet to use. | None |
| reader_dependency | titiler.core.dependencies.DefaultDependency | Endpoint dependency defining BaseReader options. | None |
| environment_dependency | Callable | Endpoint dependency to define GDAL environment at runtime. | None |
| router_prefix | str | prefix where the router will be mounted in the application. | None |
| optional_headers | sequence of titiler.core.resources.enums.OptionalHeader | additional headers to return with the response. | None |

#### Descendants

* titiler.core.factory.TilerFactory

#### Class variables

```python3
dataset_dependency
```

```python3
default_tms
```

```python3
layer_dependency
```

```python3
reader_dependency
```

```python3
render_dependency
```

```python3
router_prefix
```

```python3
supported_tms
```

```python3
templates
```

#### Methods

    
#### add_route_dependencies

```python3
def add_route_dependencies(
    self,
    *,
    scopes: List[titiler.core.routing.EndpointScope],
    dependencies=typing.List[fastapi.params.Depends]
)
```

Add dependencies to routes.

Allows a developer to add dependencies to a route after the route has been defined.

    
#### color_formula_dependency

```python3
def color_formula_dependency(
    color_formula: Annotated[Optional[str], Query(PydanticUndefined)] = None
) -> Optional[str]
```

ColorFormula Parameter.

    
#### colormap_dependency

```python3
def colormap_dependency(
    colormap_name: Annotated[Literal['flag_r', 'gist_earth_r', 'cool', 'rdpu_r', 'matter_r', 'tempo_r', 'brbg', 'bwr_r', 'wistia', 'gist_yarg', 'ylgn', 'tarn_r', 'puor', 'purd', 'bupu', 'viridis_r', 'rdylbu_r', 'thermal_r', 'purples_r', 'gnuplot', 'winter', 'twilight_shifted_r', 'gnuplot_r', 'prism', 'viridis', 'pubugn_r', 'oxy', 'haline', 'ylorbr', 'winter_r', 'solar', 'gist_heat', 'rdylbu', 'dark2', 'dark2_r', 'terrain_r', 'set3', 'gray_r', 'tab20_r', 'brbg_r', 'rdylgn', 'twilight', 'balance_r', 'summer', 'hot', 'turbid', 'diff', 'speed', 'cmrmap', 'set3_r', 'pastel1', 'piyg_r', 'deep', 'greens_r', 'inferno_r', 'curl_r', 'pubugn', 'seismic_r', 'cmrmap_r', 'hsv_r', 'ylorrd', 'dense', 'oxy_r', 'bwr', 'bone', 'set1_r', 'pastel2', 'reds', 'delta_r', 'gist_rainbow_r', 'orrd_r', 'phase_r', 'pink', 'rainbow_r', 'set2_r', 'bugn', 'ocean', 'copper', 'gist_ncar', 'cubehelix', 'spring_r', 'cool_r', 'ocean_r', 'thermal', 'tab10_r', 'cividis', 'nipy_spectral', 'copper_r', 'inferno', 'amp_r', 'speed_r', 'tab10', 'gist_earth', 'prism_r', 'rdylgn_r', 'twilight_shifted', 'pubu', 'prgn_r', 'gist_gray', 'gray', 'pubu_r', 'purd_r', 'jet', 'flag', 'ice_r', 'tab20c_r', 'paired_r', 'cividis_r', 'gnbu_r', 'autumn_r', 'cfastie', 'spring', 'magma_r', 'rain_r', 'bugn_r', 'afmhot', 'pastel2_r', 'brg_r', 'puor_r', 'nipy_spectral_r', 'gist_stern', 'phase', 'deep_r', 'tempo', 'gist_ncar_r', 'amp', 'balance', 'spectral', 'cubehelix_r', 'delta', 'rain', 'diff_r', 'magma', 'greens', 'reds_r', 'gist_heat_r', 'piyg', 'set1', 'topo_r', 'bone_r', 'binary_r', 'tab20c', 'rdgy_r', 'wistia_r', 'topo', 'algae_r', 'autumn', 'gist_yarg_r', 'ylorrd_r', 'rdbu_r', 'pink_r', 'paired', 'matter', 'terrain', 'twilight_r', 'oranges', 'brg', 'ylgnbu_r', 'purples', 'set2', 'plasma', 'ylorbr_r', 'spectral_r', 'plasma_r', 'coolwarm', 'turbo_r', 'binary', 'schwarzwald', 'rdpu', 'greys_r', 'coolwarm_r', 'tarn', 'algae', 'oranges_r', 'rainbow', 'orrd', 'curl', 'accent', 'rplumbo', 'afmhot_r', 'turbo', 'hsv', 'ylgn_r', 'blues', 'tab20b', 'accent_r', 'ice', 'gist_stern_r', 'blues_r', 'rdbu', 'hot_r', 'jet_r', 'seismic', 'summer_r', 'ylgnbu', 'tab20b_r', 'pastel1_r', 'rdgy', 'gist_rainbow', 'dense_r', 'turbid_r', 'bupu_r', 'solar_r', 'gnbu', 'prgn', 'greys', 'tab20', 'haline_r', 'gist_gray_r', 'gnuplot2_r', 'gnuplot2'], Query(PydanticUndefined)] = None,
    colormap: Annotated[Optional[str], Query(PydanticUndefined)] = None
)
```

    
#### environment_dependency

```python3
def environment_dependency(
    
)
```

    
#### path_dependency

```python3
def path_dependency(
    url: typing.Annotated[str, Query(PydanticUndefined)]
) -> str
```

Create dataset path from args

    
#### process_dependency

```python3
def process_dependency(
    algorithm: Annotated[Literal['hillshade', 'contours', 'normalizedIndex', 'terrarium', 'terrainrgb'], Query(PydanticUndefined)] = None,
    algorithm_params: Annotated[Optional[str], Query(PydanticUndefined)] = None
) -> Optional[titiler.core.algorithm.base.BaseAlgorithm]
```

Data Post-Processing options.

    
#### register_routes

```python3
def register_routes(
    self
)
```

Register Tiler Routes.

    
#### rescale_dependency

```python3
def rescale_dependency(
    rescale: Annotated[Optional[List[str]], Query(PydanticUndefined)] = None
) -> Optional[List[Tuple[float, ...]]]
```

Min/Max data Rescaling

    
#### url_for

```python3
def url_for(
    self,
    request: starlette.requests.Request,
    name: str,
    **path_params: Any
) -> str
```

Return full url (with prefix) for a specific endpoint.

### ColorMapFactory

```python3
class ColorMapFactory(
    supported_colormaps: rio_tiler.colormap.ColorMaps = ColorMaps(data={'flag_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/flag_r.npy', 'gist_earth_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gist_earth_r.npy', 'cool': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/cool.npy', 'rdpu_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/rdpu_r.npy', 'matter_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/matter_r.npy', 'tempo_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/tempo_r.npy', 'brbg': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/brbg.npy', 'bwr_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/bwr_r.npy', 'wistia': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/wistia.npy', 'gist_yarg': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gist_yarg.npy', 'ylgn': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/ylgn.npy', 'tarn_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/tarn_r.npy', 'puor': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/puor.npy', 'purd': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/purd.npy', 'bupu': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/bupu.npy', 'viridis_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/viridis_r.npy', 'rdylbu_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/rdylbu_r.npy', 'thermal_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/thermal_r.npy', 'purples_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/purples_r.npy', 'gnuplot': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gnuplot.npy', 'winter': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/winter.npy', 'twilight_shifted_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/twilight_shifted_r.npy', 'gnuplot_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gnuplot_r.npy', 'prism': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/prism.npy', 'viridis': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/viridis.npy', 'pubugn_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/pubugn_r.npy', 'oxy': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/oxy.npy', 'haline': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/haline.npy', 'ylorbr': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/ylorbr.npy', 'winter_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/winter_r.npy', 'solar': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/solar.npy', 'gist_heat': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gist_heat.npy', 'rdylbu': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/rdylbu.npy', 'dark2': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/dark2.npy', 'dark2_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/dark2_r.npy', 'terrain_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/terrain_r.npy', 'set3': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/set3.npy', 'gray_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gray_r.npy', 'tab20_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/tab20_r.npy', 'brbg_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/brbg_r.npy', 'rdylgn': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/rdylgn.npy', 'twilight': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/twilight.npy', 'balance_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/balance_r.npy', 'summer': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/summer.npy', 'hot': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/hot.npy', 'turbid': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/turbid.npy', 'diff': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/diff.npy', 'speed': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/speed.npy', 'cmrmap': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/cmrmap.npy', 'set3_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/set3_r.npy', 'pastel1': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/pastel1.npy', 'piyg_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/piyg_r.npy', 'deep': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/deep.npy', 'greens_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/greens_r.npy', 'inferno_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/inferno_r.npy', 'curl_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/curl_r.npy', 'pubugn': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/pubugn.npy', 'seismic_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/seismic_r.npy', 'cmrmap_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/cmrmap_r.npy', 'hsv_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/hsv_r.npy', 'ylorrd': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/ylorrd.npy', 'dense': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/dense.npy', 'oxy_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/oxy_r.npy', 'bwr': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/bwr.npy', 'bone': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/bone.npy', 'set1_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/set1_r.npy', 'pastel2': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/pastel2.npy', 'reds': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/reds.npy', 'delta_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/delta_r.npy', 'gist_rainbow_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gist_rainbow_r.npy', 'orrd_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/orrd_r.npy', 'phase_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/phase_r.npy', 'pink': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/pink.npy', 'rainbow_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/rainbow_r.npy', 'set2_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/set2_r.npy', 'bugn': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/bugn.npy', 'ocean': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/ocean.npy', 'copper': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/copper.npy', 'gist_ncar': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gist_ncar.npy', 'cubehelix': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/cubehelix.npy', 'spring_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/spring_r.npy', 'cool_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/cool_r.npy', 'ocean_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/ocean_r.npy', 'thermal': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/thermal.npy', 'tab10_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/tab10_r.npy', 'cividis': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/cividis.npy', 'nipy_spectral': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/nipy_spectral.npy', 'copper_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/copper_r.npy', 'inferno': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/inferno.npy', 'amp_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/amp_r.npy', 'speed_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/speed_r.npy', 'tab10': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/tab10.npy', 'gist_earth': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gist_earth.npy', 'prism_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/prism_r.npy', 'rdylgn_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/rdylgn_r.npy', 'twilight_shifted': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/twilight_shifted.npy', 'pubu': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/pubu.npy', 'prgn_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/prgn_r.npy', 'gist_gray': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gist_gray.npy', 'gray': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gray.npy', 'pubu_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/pubu_r.npy', 'purd_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/purd_r.npy', 'jet': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/jet.npy', 'flag': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/flag.npy', 'ice_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/ice_r.npy', 'tab20c_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/tab20c_r.npy', 'paired_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/paired_r.npy', 'cividis_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/cividis_r.npy', 'gnbu_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gnbu_r.npy', 'autumn_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/autumn_r.npy', 'cfastie': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/cfastie.npy', 'spring': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/spring.npy', 'magma_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/magma_r.npy', 'rain_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/rain_r.npy', 'bugn_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/bugn_r.npy', 'afmhot': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/afmhot.npy', 'pastel2_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/pastel2_r.npy', 'brg_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/brg_r.npy', 'puor_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/puor_r.npy', 'nipy_spectral_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/nipy_spectral_r.npy', 'gist_stern': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gist_stern.npy', 'phase': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/phase.npy', 'deep_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/deep_r.npy', 'tempo': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/tempo.npy', 'gist_ncar_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gist_ncar_r.npy', 'amp': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/amp.npy', 'balance': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/balance.npy', 'spectral': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/spectral.npy', 'cubehelix_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/cubehelix_r.npy', 'delta': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/delta.npy', 'rain': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/rain.npy', 'diff_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/diff_r.npy', 'magma': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/magma.npy', 'greens': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/greens.npy', 'reds_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/reds_r.npy', 'gist_heat_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gist_heat_r.npy', 'piyg': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/piyg.npy', 'set1': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/set1.npy', 'topo_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/topo_r.npy', 'bone_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/bone_r.npy', 'binary_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/binary_r.npy', 'tab20c': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/tab20c.npy', 'rdgy_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/rdgy_r.npy', 'wistia_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/wistia_r.npy', 'topo': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/topo.npy', 'algae_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/algae_r.npy', 'autumn': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/autumn.npy', 'gist_yarg_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gist_yarg_r.npy', 'ylorrd_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/ylorrd_r.npy', 'rdbu_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/rdbu_r.npy', 'pink_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/pink_r.npy', 'paired': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/paired.npy', 'matter': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/matter.npy', 'terrain': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/terrain.npy', 'twilight_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/twilight_r.npy', 'oranges': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/oranges.npy', 'brg': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/brg.npy', 'ylgnbu_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/ylgnbu_r.npy', 'purples': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/purples.npy', 'set2': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/set2.npy', 'plasma': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/plasma.npy', 'ylorbr_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/ylorbr_r.npy', 'spectral_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/spectral_r.npy', 'plasma_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/plasma_r.npy', 'coolwarm': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/coolwarm.npy', 'turbo_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/turbo_r.npy', 'binary': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/binary.npy', 'schwarzwald': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/schwarzwald.npy', 'rdpu': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/rdpu.npy', 'greys_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/greys_r.npy', 'coolwarm_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/coolwarm_r.npy', 'tarn': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/tarn.npy', 'algae': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/algae.npy', 'oranges_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/oranges_r.npy', 'rainbow': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/rainbow.npy', 'orrd': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/orrd.npy', 'curl': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/curl.npy', 'accent': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/accent.npy', 'rplumbo': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/rplumbo.npy', 'afmhot_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/afmhot_r.npy', 'turbo': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/turbo.npy', 'hsv': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/hsv.npy', 'ylgn_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/ylgn_r.npy', 'blues': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/blues.npy', 'tab20b': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/tab20b.npy', 'accent_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/accent_r.npy', 'ice': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/ice.npy', 'gist_stern_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gist_stern_r.npy', 'blues_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/blues_r.npy', 'rdbu': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/rdbu.npy', 'hot_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/hot_r.npy', 'jet_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/jet_r.npy', 'seismic': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/seismic.npy', 'summer_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/summer_r.npy', 'ylgnbu': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/ylgnbu.npy', 'tab20b_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/tab20b_r.npy', 'pastel1_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/pastel1_r.npy', 'rdgy': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/rdgy.npy', 'gist_rainbow': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gist_rainbow.npy', 'dense_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/dense_r.npy', 'turbid_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/turbid_r.npy', 'bupu_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/bupu_r.npy', 'solar_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/solar_r.npy', 'gnbu': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gnbu.npy', 'prgn': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/prgn.npy', 'greys': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/greys.npy', 'tab20': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/tab20.npy', 'haline_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/haline_r.npy', 'gist_gray_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gist_gray_r.npy', 'gnuplot2_r': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gnuplot2_r.npy', 'gnuplot2': '/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/rio_tiler/cmap_data/gnuplot2.npy'}),
    router: fastapi.routing.APIRouter = <factory>
)
```

Colormap endpoints Factory.

#### Class variables

```python3
supported_colormaps
```

#### Methods

    
#### url_for

```python3
def url_for(
    self,
    request: starlette.requests.Request,
    name: str,
    **path_params: Any
) -> str
```

Return full url (with prefix) for a specific endpoint.

### FactoryExtension

```python3
class FactoryExtension(
    
)
```

Factory Extension.

#### Methods

    
#### register

```python3
def register(
    self,
    factory: 'BaseTilerFactory'
)
```

Register extension to the factory.

### MultiBandTilerFactory

```python3
class MultiBandTilerFactory(
    reader: Type[rio_tiler.io.base.MultiBandReader] = <class 'rio_tiler.io.rasterio.Reader'>,
    router: fastapi.routing.APIRouter = <factory>,
    path_dependency: Callable[..., Any] = <function DatasetPathParams at 0x7f1b17ce37e0>,
    layer_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.BandsExprParams'>,
    dataset_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.DatasetParams'>,
    process_dependency: Callable[..., Optional[titiler.core.algorithm.base.BaseAlgorithm]] = <function Algorithms.dependency.<locals>.post_process at 0x7f1b0d806160>,
    rescale_dependency: Callable[..., Optional[List[Tuple[float, ...]]]] = <function RescalingParams at 0x7f1b0db8f880>,
    color_formula_dependency: Callable[..., Optional[str]] = <function ColorFormulaParams at 0x7f1b0dbb6fc0>,
    colormap_dependency: Callable[..., Union[Dict[int, Tuple[int, int, int, int]], Sequence[Tuple[Tuple[Union[float, int], Union[float, int]], Tuple[int, int, int, int]]], NoneType]] = <function create_colormap_dependency.<locals>.deps at 0x7f1b17ce3560>,
    render_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.ImageRenderingParams'>,
    reader_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.DefaultDependency'>,
    environment_dependency: Callable[..., Dict] = <function BaseTilerFactory.<lambda> at 0x7f1b0d806200>,
    supported_tms: morecantile.defaults.TileMatrixSets = TileMatrixSets(tms={'CDB1GlobalGrid': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/CDB1GlobalGrid.json'), 'CanadianNAD83_LCC': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/CanadianNAD83_LCC.json'), 'EuropeanETRS89_LAEAQuad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/EuropeanETRS89_LAEAQuad.json'), 'GNOSISGlobalGrid': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/GNOSISGlobalGrid.json'), 'LINZAntarticaMapTilegrid': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/LINZAntarticaMapTilegrid.json'), 'NZTM2000Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/NZTM2000Quad.json'), 'UPSAntarcticWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/UPSAntarcticWGS84Quad.json'), 'UPSArcticWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/UPSArcticWGS84Quad.json'), 'UTM31WGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/UTM31WGS84Quad.json'), 'WGS1984Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/WGS1984Quad.json'), 'WebMercatorQuad': <TileMatrixSet title='Google Maps Compatible for the World' id='WebMercatorQuad' crs='http://www.opengis.net/def/crs/EPSG/0/3857>, 'WorldCRS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/WorldCRS84Quad.json'), 'WorldMercatorWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/WorldMercatorWGS84Quad.json')}),
    default_tms: Optional[str] = None,
    router_prefix: str = '',
    optional_headers: List[titiler.core.resources.enums.OptionalHeader] = <factory>,
    route_dependencies: List[Tuple[List[titiler.core.routing.EndpointScope], List[fastapi.params.Depends]]] = <factory>,
    extensions: List[titiler.core.factory.FactoryExtension] = <factory>,
    templates: starlette.templating.Jinja2Templates = <starlette.templating.Jinja2Templates object at 0x7f1b0d93cd10>,
    stats_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.StatisticsParams'>,
    histogram_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.HistogramParams'>,
    img_preview_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.PreviewParams'>,
    img_part_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.PartFeatureParams'>,
    tile_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.TileParams'>,
    add_preview: bool = True,
    add_part: bool = True,
    add_viewer: bool = True,
    bands_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.BandsParams'>
)
```

Custom Tiler Factory for MultiBandReader classes.

Note:
    To be able to use the rio_tiler.io.MultiBandReader we need to be able to pass a `bands`
    argument to most of its methods. By using the `BandsExprParams` for the `layer_dependency`, the
    .tile(), .point(), .preview() and the .part() methods will receive bands or expression arguments.

    The rio_tiler.io.MultiBandReader  `.info()` and `.metadata()` have `bands` as
    a requirement arguments (https://github.com/cogeotiff/rio-tiler/blob/main/rio_tiler/io/base.py#L775).
    This means we have to update the /info and /metadata endpoints in order to add the `bands` dependency.

    For implementation example see https://github.com/developmentseed/titiler-pds

#### Ancestors (in MRO)

* titiler.core.factory.TilerFactory
* titiler.core.factory.BaseTilerFactory

#### Class variables

```python3
add_part
```

```python3
add_preview
```

```python3
add_viewer
```

```python3
bands_dependency
```

```python3
dataset_dependency
```

```python3
default_tms
```

```python3
histogram_dependency
```

```python3
img_part_dependency
```

```python3
img_preview_dependency
```

```python3
layer_dependency
```

```python3
reader
```

```python3
reader_dependency
```

```python3
render_dependency
```

```python3
router_prefix
```

```python3
stats_dependency
```

```python3
supported_tms
```

```python3
templates
```

```python3
tile_dependency
```

#### Methods

    
#### add_route_dependencies

```python3
def add_route_dependencies(
    self,
    *,
    scopes: List[titiler.core.routing.EndpointScope],
    dependencies=typing.List[fastapi.params.Depends]
)
```

Add dependencies to routes.

Allows a developer to add dependencies to a route after the route has been defined.

    
#### bounds

```python3
def bounds(
    self
)
```

Register /bounds endpoint.

    
#### color_formula_dependency

```python3
def color_formula_dependency(
    color_formula: Annotated[Optional[str], Query(PydanticUndefined)] = None
) -> Optional[str]
```

ColorFormula Parameter.

    
#### colormap_dependency

```python3
def colormap_dependency(
    colormap_name: Annotated[Literal['flag_r', 'gist_earth_r', 'cool', 'rdpu_r', 'matter_r', 'tempo_r', 'brbg', 'bwr_r', 'wistia', 'gist_yarg', 'ylgn', 'tarn_r', 'puor', 'purd', 'bupu', 'viridis_r', 'rdylbu_r', 'thermal_r', 'purples_r', 'gnuplot', 'winter', 'twilight_shifted_r', 'gnuplot_r', 'prism', 'viridis', 'pubugn_r', 'oxy', 'haline', 'ylorbr', 'winter_r', 'solar', 'gist_heat', 'rdylbu', 'dark2', 'dark2_r', 'terrain_r', 'set3', 'gray_r', 'tab20_r', 'brbg_r', 'rdylgn', 'twilight', 'balance_r', 'summer', 'hot', 'turbid', 'diff', 'speed', 'cmrmap', 'set3_r', 'pastel1', 'piyg_r', 'deep', 'greens_r', 'inferno_r', 'curl_r', 'pubugn', 'seismic_r', 'cmrmap_r', 'hsv_r', 'ylorrd', 'dense', 'oxy_r', 'bwr', 'bone', 'set1_r', 'pastel2', 'reds', 'delta_r', 'gist_rainbow_r', 'orrd_r', 'phase_r', 'pink', 'rainbow_r', 'set2_r', 'bugn', 'ocean', 'copper', 'gist_ncar', 'cubehelix', 'spring_r', 'cool_r', 'ocean_r', 'thermal', 'tab10_r', 'cividis', 'nipy_spectral', 'copper_r', 'inferno', 'amp_r', 'speed_r', 'tab10', 'gist_earth', 'prism_r', 'rdylgn_r', 'twilight_shifted', 'pubu', 'prgn_r', 'gist_gray', 'gray', 'pubu_r', 'purd_r', 'jet', 'flag', 'ice_r', 'tab20c_r', 'paired_r', 'cividis_r', 'gnbu_r', 'autumn_r', 'cfastie', 'spring', 'magma_r', 'rain_r', 'bugn_r', 'afmhot', 'pastel2_r', 'brg_r', 'puor_r', 'nipy_spectral_r', 'gist_stern', 'phase', 'deep_r', 'tempo', 'gist_ncar_r', 'amp', 'balance', 'spectral', 'cubehelix_r', 'delta', 'rain', 'diff_r', 'magma', 'greens', 'reds_r', 'gist_heat_r', 'piyg', 'set1', 'topo_r', 'bone_r', 'binary_r', 'tab20c', 'rdgy_r', 'wistia_r', 'topo', 'algae_r', 'autumn', 'gist_yarg_r', 'ylorrd_r', 'rdbu_r', 'pink_r', 'paired', 'matter', 'terrain', 'twilight_r', 'oranges', 'brg', 'ylgnbu_r', 'purples', 'set2', 'plasma', 'ylorbr_r', 'spectral_r', 'plasma_r', 'coolwarm', 'turbo_r', 'binary', 'schwarzwald', 'rdpu', 'greys_r', 'coolwarm_r', 'tarn', 'algae', 'oranges_r', 'rainbow', 'orrd', 'curl', 'accent', 'rplumbo', 'afmhot_r', 'turbo', 'hsv', 'ylgn_r', 'blues', 'tab20b', 'accent_r', 'ice', 'gist_stern_r', 'blues_r', 'rdbu', 'hot_r', 'jet_r', 'seismic', 'summer_r', 'ylgnbu', 'tab20b_r', 'pastel1_r', 'rdgy', 'gist_rainbow', 'dense_r', 'turbid_r', 'bupu_r', 'solar_r', 'gnbu', 'prgn', 'greys', 'tab20', 'haline_r', 'gist_gray_r', 'gnuplot2_r', 'gnuplot2'], Query(PydanticUndefined)] = None,
    colormap: Annotated[Optional[str], Query(PydanticUndefined)] = None
)
```

    
#### environment_dependency

```python3
def environment_dependency(
    
)
```

    
#### info

```python3
def info(
    self
)
```

Register /info endpoint.

    
#### map_viewer

```python3
def map_viewer(
    self
)
```

Register /map endpoint.

    
#### part

```python3
def part(
    self
)
```

Register /bbox and `/feature` endpoints.

    
#### path_dependency

```python3
def path_dependency(
    url: typing.Annotated[str, Query(PydanticUndefined)]
) -> str
```

Create dataset path from args

    
#### point

```python3
def point(
    self
)
```

Register /point endpoints.

    
#### preview

```python3
def preview(
    self
)
```

Register /preview endpoint.

    
#### process_dependency

```python3
def process_dependency(
    algorithm: Annotated[Literal['hillshade', 'contours', 'normalizedIndex', 'terrarium', 'terrainrgb'], Query(PydanticUndefined)] = None,
    algorithm_params: Annotated[Optional[str], Query(PydanticUndefined)] = None
) -> Optional[titiler.core.algorithm.base.BaseAlgorithm]
```

Data Post-Processing options.

    
#### register_routes

```python3
def register_routes(
    self
)
```

This Method register routes to the router.

Because we wrap the endpoints in a class we cannot define the routes as
methods (because of the self argument). The HACK is to define routes inside
the class method and register them after the class initialization.

    
#### rescale_dependency

```python3
def rescale_dependency(
    rescale: Annotated[Optional[List[str]], Query(PydanticUndefined)] = None
) -> Optional[List[Tuple[float, ...]]]
```

Min/Max data Rescaling

    
#### statistics

```python3
def statistics(
    self
)
```

add statistics endpoints.

    
#### tile

```python3
def tile(
    self
)
```

Register /tiles endpoint.

    
#### tilejson

```python3
def tilejson(
    self
)
```

Register /tilejson.json endpoint.

    
#### url_for

```python3
def url_for(
    self,
    request: starlette.requests.Request,
    name: str,
    **path_params: Any
) -> str
```

Return full url (with prefix) for a specific endpoint.

    
#### wmts

```python3
def wmts(
    self
)
```

Register /wmts endpoint.

### MultiBaseTilerFactory

```python3
class MultiBaseTilerFactory(
    reader: Type[rio_tiler.io.base.MultiBaseReader] = <class 'rio_tiler.io.rasterio.Reader'>,
    router: fastapi.routing.APIRouter = <factory>,
    path_dependency: Callable[..., Any] = <function DatasetPathParams at 0x7f1b17ce37e0>,
    layer_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.AssetsBidxExprParams'>,
    dataset_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.DatasetParams'>,
    process_dependency: Callable[..., Optional[titiler.core.algorithm.base.BaseAlgorithm]] = <function Algorithms.dependency.<locals>.post_process at 0x7f1b0d806160>,
    rescale_dependency: Callable[..., Optional[List[Tuple[float, ...]]]] = <function RescalingParams at 0x7f1b0db8f880>,
    color_formula_dependency: Callable[..., Optional[str]] = <function ColorFormulaParams at 0x7f1b0dbb6fc0>,
    colormap_dependency: Callable[..., Union[Dict[int, Tuple[int, int, int, int]], Sequence[Tuple[Tuple[Union[float, int], Union[float, int]], Tuple[int, int, int, int]]], NoneType]] = <function create_colormap_dependency.<locals>.deps at 0x7f1b17ce3560>,
    render_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.ImageRenderingParams'>,
    reader_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.DefaultDependency'>,
    environment_dependency: Callable[..., Dict] = <function BaseTilerFactory.<lambda> at 0x7f1b0d806200>,
    supported_tms: morecantile.defaults.TileMatrixSets = TileMatrixSets(tms={'CDB1GlobalGrid': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/CDB1GlobalGrid.json'), 'CanadianNAD83_LCC': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/CanadianNAD83_LCC.json'), 'EuropeanETRS89_LAEAQuad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/EuropeanETRS89_LAEAQuad.json'), 'GNOSISGlobalGrid': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/GNOSISGlobalGrid.json'), 'LINZAntarticaMapTilegrid': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/LINZAntarticaMapTilegrid.json'), 'NZTM2000Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/NZTM2000Quad.json'), 'UPSAntarcticWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/UPSAntarcticWGS84Quad.json'), 'UPSArcticWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/UPSArcticWGS84Quad.json'), 'UTM31WGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/UTM31WGS84Quad.json'), 'WGS1984Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/WGS1984Quad.json'), 'WebMercatorQuad': <TileMatrixSet title='Google Maps Compatible for the World' id='WebMercatorQuad' crs='http://www.opengis.net/def/crs/EPSG/0/3857>, 'WorldCRS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/WorldCRS84Quad.json'), 'WorldMercatorWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/WorldMercatorWGS84Quad.json')}),
    default_tms: Optional[str] = None,
    router_prefix: str = '',
    optional_headers: List[titiler.core.resources.enums.OptionalHeader] = <factory>,
    route_dependencies: List[Tuple[List[titiler.core.routing.EndpointScope], List[fastapi.params.Depends]]] = <factory>,
    extensions: List[titiler.core.factory.FactoryExtension] = <factory>,
    templates: starlette.templating.Jinja2Templates = <starlette.templating.Jinja2Templates object at 0x7f1b0d93cd10>,
    stats_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.StatisticsParams'>,
    histogram_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.HistogramParams'>,
    img_preview_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.PreviewParams'>,
    img_part_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.PartFeatureParams'>,
    tile_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.TileParams'>,
    add_preview: bool = True,
    add_part: bool = True,
    add_viewer: bool = True,
    assets_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.AssetsParams'>
)
```

Custom Tiler Factory for MultiBaseReader classes.

Note:
    To be able to use the rio_tiler.io.MultiBaseReader we need to be able to pass a `assets`
    argument to most of its methods. By using the `AssetsBidxExprParams` for the `layer_dependency`, the
    .tile(), .point(), .preview() and the .part() methods will receive assets, expression or indexes arguments.

    The rio_tiler.io.MultiBaseReader  `.info()` and `.metadata()` have `assets` as
    a requirement arguments (https://github.com/cogeotiff/rio-tiler/blob/main/rio_tiler/io/base.py#L365).
    This means we have to update the /info and /metadata endpoints in order to add the `assets` dependency.

#### Ancestors (in MRO)

* titiler.core.factory.TilerFactory
* titiler.core.factory.BaseTilerFactory

#### Class variables

```python3
add_part
```

```python3
add_preview
```

```python3
add_viewer
```

```python3
assets_dependency
```

```python3
dataset_dependency
```

```python3
default_tms
```

```python3
histogram_dependency
```

```python3
img_part_dependency
```

```python3
img_preview_dependency
```

```python3
layer_dependency
```

```python3
reader
```

```python3
reader_dependency
```

```python3
render_dependency
```

```python3
router_prefix
```

```python3
stats_dependency
```

```python3
supported_tms
```

```python3
templates
```

```python3
tile_dependency
```

#### Methods

    
#### add_route_dependencies

```python3
def add_route_dependencies(
    self,
    *,
    scopes: List[titiler.core.routing.EndpointScope],
    dependencies=typing.List[fastapi.params.Depends]
)
```

Add dependencies to routes.

Allows a developer to add dependencies to a route after the route has been defined.

    
#### bounds

```python3
def bounds(
    self
)
```

Register /bounds endpoint.

    
#### color_formula_dependency

```python3
def color_formula_dependency(
    color_formula: Annotated[Optional[str], Query(PydanticUndefined)] = None
) -> Optional[str]
```

ColorFormula Parameter.

    
#### colormap_dependency

```python3
def colormap_dependency(
    colormap_name: Annotated[Literal['flag_r', 'gist_earth_r', 'cool', 'rdpu_r', 'matter_r', 'tempo_r', 'brbg', 'bwr_r', 'wistia', 'gist_yarg', 'ylgn', 'tarn_r', 'puor', 'purd', 'bupu', 'viridis_r', 'rdylbu_r', 'thermal_r', 'purples_r', 'gnuplot', 'winter', 'twilight_shifted_r', 'gnuplot_r', 'prism', 'viridis', 'pubugn_r', 'oxy', 'haline', 'ylorbr', 'winter_r', 'solar', 'gist_heat', 'rdylbu', 'dark2', 'dark2_r', 'terrain_r', 'set3', 'gray_r', 'tab20_r', 'brbg_r', 'rdylgn', 'twilight', 'balance_r', 'summer', 'hot', 'turbid', 'diff', 'speed', 'cmrmap', 'set3_r', 'pastel1', 'piyg_r', 'deep', 'greens_r', 'inferno_r', 'curl_r', 'pubugn', 'seismic_r', 'cmrmap_r', 'hsv_r', 'ylorrd', 'dense', 'oxy_r', 'bwr', 'bone', 'set1_r', 'pastel2', 'reds', 'delta_r', 'gist_rainbow_r', 'orrd_r', 'phase_r', 'pink', 'rainbow_r', 'set2_r', 'bugn', 'ocean', 'copper', 'gist_ncar', 'cubehelix', 'spring_r', 'cool_r', 'ocean_r', 'thermal', 'tab10_r', 'cividis', 'nipy_spectral', 'copper_r', 'inferno', 'amp_r', 'speed_r', 'tab10', 'gist_earth', 'prism_r', 'rdylgn_r', 'twilight_shifted', 'pubu', 'prgn_r', 'gist_gray', 'gray', 'pubu_r', 'purd_r', 'jet', 'flag', 'ice_r', 'tab20c_r', 'paired_r', 'cividis_r', 'gnbu_r', 'autumn_r', 'cfastie', 'spring', 'magma_r', 'rain_r', 'bugn_r', 'afmhot', 'pastel2_r', 'brg_r', 'puor_r', 'nipy_spectral_r', 'gist_stern', 'phase', 'deep_r', 'tempo', 'gist_ncar_r', 'amp', 'balance', 'spectral', 'cubehelix_r', 'delta', 'rain', 'diff_r', 'magma', 'greens', 'reds_r', 'gist_heat_r', 'piyg', 'set1', 'topo_r', 'bone_r', 'binary_r', 'tab20c', 'rdgy_r', 'wistia_r', 'topo', 'algae_r', 'autumn', 'gist_yarg_r', 'ylorrd_r', 'rdbu_r', 'pink_r', 'paired', 'matter', 'terrain', 'twilight_r', 'oranges', 'brg', 'ylgnbu_r', 'purples', 'set2', 'plasma', 'ylorbr_r', 'spectral_r', 'plasma_r', 'coolwarm', 'turbo_r', 'binary', 'schwarzwald', 'rdpu', 'greys_r', 'coolwarm_r', 'tarn', 'algae', 'oranges_r', 'rainbow', 'orrd', 'curl', 'accent', 'rplumbo', 'afmhot_r', 'turbo', 'hsv', 'ylgn_r', 'blues', 'tab20b', 'accent_r', 'ice', 'gist_stern_r', 'blues_r', 'rdbu', 'hot_r', 'jet_r', 'seismic', 'summer_r', 'ylgnbu', 'tab20b_r', 'pastel1_r', 'rdgy', 'gist_rainbow', 'dense_r', 'turbid_r', 'bupu_r', 'solar_r', 'gnbu', 'prgn', 'greys', 'tab20', 'haline_r', 'gist_gray_r', 'gnuplot2_r', 'gnuplot2'], Query(PydanticUndefined)] = None,
    colormap: Annotated[Optional[str], Query(PydanticUndefined)] = None
)
```

    
#### environment_dependency

```python3
def environment_dependency(
    
)
```

    
#### info

```python3
def info(
    self
)
```

Register /info endpoint.

    
#### map_viewer

```python3
def map_viewer(
    self
)
```

Register /map endpoint.

    
#### part

```python3
def part(
    self
)
```

Register /bbox and `/feature` endpoints.

    
#### path_dependency

```python3
def path_dependency(
    url: typing.Annotated[str, Query(PydanticUndefined)]
) -> str
```

Create dataset path from args

    
#### point

```python3
def point(
    self
)
```

Register /point endpoints.

    
#### preview

```python3
def preview(
    self
)
```

Register /preview endpoint.

    
#### process_dependency

```python3
def process_dependency(
    algorithm: Annotated[Literal['hillshade', 'contours', 'normalizedIndex', 'terrarium', 'terrainrgb'], Query(PydanticUndefined)] = None,
    algorithm_params: Annotated[Optional[str], Query(PydanticUndefined)] = None
) -> Optional[titiler.core.algorithm.base.BaseAlgorithm]
```

Data Post-Processing options.

    
#### register_routes

```python3
def register_routes(
    self
)
```

This Method register routes to the router.

Because we wrap the endpoints in a class we cannot define the routes as
methods (because of the self argument). The HACK is to define routes inside
the class method and register them after the class initialization.

    
#### rescale_dependency

```python3
def rescale_dependency(
    rescale: Annotated[Optional[List[str]], Query(PydanticUndefined)] = None
) -> Optional[List[Tuple[float, ...]]]
```

Min/Max data Rescaling

    
#### statistics

```python3
def statistics(
    self
)
```

Register /statistics endpoint.

    
#### tile

```python3
def tile(
    self
)
```

Register /tiles endpoint.

    
#### tilejson

```python3
def tilejson(
    self
)
```

Register /tilejson.json endpoint.

    
#### url_for

```python3
def url_for(
    self,
    request: starlette.requests.Request,
    name: str,
    **path_params: Any
) -> str
```

Return full url (with prefix) for a specific endpoint.

    
#### wmts

```python3
def wmts(
    self
)
```

Register /wmts endpoint.

### TMSFactory

```python3
class TMSFactory(
    supported_tms: morecantile.defaults.TileMatrixSets = TileMatrixSets(tms={'CDB1GlobalGrid': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/CDB1GlobalGrid.json'), 'CanadianNAD83_LCC': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/CanadianNAD83_LCC.json'), 'EuropeanETRS89_LAEAQuad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/EuropeanETRS89_LAEAQuad.json'), 'GNOSISGlobalGrid': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/GNOSISGlobalGrid.json'), 'LINZAntarticaMapTilegrid': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/LINZAntarticaMapTilegrid.json'), 'NZTM2000Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/NZTM2000Quad.json'), 'UPSAntarcticWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/UPSAntarcticWGS84Quad.json'), 'UPSArcticWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/UPSArcticWGS84Quad.json'), 'UTM31WGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/UTM31WGS84Quad.json'), 'WGS1984Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/WGS1984Quad.json'), 'WebMercatorQuad': <TileMatrixSet title='Google Maps Compatible for the World' id='WebMercatorQuad' crs='http://www.opengis.net/def/crs/EPSG/0/3857>, 'WorldCRS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/WorldCRS84Quad.json'), 'WorldMercatorWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/WorldMercatorWGS84Quad.json')}),
    router: fastapi.routing.APIRouter = <factory>,
    router_prefix: str = ''
)
```

TileMatrixSet endpoints Factory.

#### Class variables

```python3
router_prefix
```

```python3
supported_tms
```

#### Methods

    
#### register_routes

```python3
def register_routes(
    self
)
```

Register TMS endpoint routes.

    
#### url_for

```python3
def url_for(
    self,
    request: starlette.requests.Request,
    name: str,
    **path_params: Any
) -> str
```

Return full url (with prefix) for a specific endpoint.

### TilerFactory

```python3
class TilerFactory(
    reader: Type[rio_tiler.io.base.BaseReader] = <class 'rio_tiler.io.rasterio.Reader'>,
    router: fastapi.routing.APIRouter = <factory>,
    path_dependency: Callable[..., Any] = <function DatasetPathParams at 0x7f1b17ce37e0>,
    layer_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.BidxExprParams'>,
    dataset_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.DatasetParams'>,
    process_dependency: Callable[..., Optional[titiler.core.algorithm.base.BaseAlgorithm]] = <function Algorithms.dependency.<locals>.post_process at 0x7f1b0d806160>,
    rescale_dependency: Callable[..., Optional[List[Tuple[float, ...]]]] = <function RescalingParams at 0x7f1b0db8f880>,
    color_formula_dependency: Callable[..., Optional[str]] = <function ColorFormulaParams at 0x7f1b0dbb6fc0>,
    colormap_dependency: Callable[..., Union[Dict[int, Tuple[int, int, int, int]], Sequence[Tuple[Tuple[Union[float, int], Union[float, int]], Tuple[int, int, int, int]]], NoneType]] = <function create_colormap_dependency.<locals>.deps at 0x7f1b17ce3560>,
    render_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.ImageRenderingParams'>,
    reader_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.DefaultDependency'>,
    environment_dependency: Callable[..., Dict] = <function BaseTilerFactory.<lambda> at 0x7f1b0d806200>,
    supported_tms: morecantile.defaults.TileMatrixSets = TileMatrixSets(tms={'CDB1GlobalGrid': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/CDB1GlobalGrid.json'), 'CanadianNAD83_LCC': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/CanadianNAD83_LCC.json'), 'EuropeanETRS89_LAEAQuad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/EuropeanETRS89_LAEAQuad.json'), 'GNOSISGlobalGrid': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/GNOSISGlobalGrid.json'), 'LINZAntarticaMapTilegrid': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/LINZAntarticaMapTilegrid.json'), 'NZTM2000Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/NZTM2000Quad.json'), 'UPSAntarcticWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/UPSAntarcticWGS84Quad.json'), 'UPSArcticWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/UPSArcticWGS84Quad.json'), 'UTM31WGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/UTM31WGS84Quad.json'), 'WGS1984Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/WGS1984Quad.json'), 'WebMercatorQuad': <TileMatrixSet title='Google Maps Compatible for the World' id='WebMercatorQuad' crs='http://www.opengis.net/def/crs/EPSG/0/3857>, 'WorldCRS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/WorldCRS84Quad.json'), 'WorldMercatorWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/WorldMercatorWGS84Quad.json')}),
    default_tms: Optional[str] = None,
    router_prefix: str = '',
    optional_headers: List[titiler.core.resources.enums.OptionalHeader] = <factory>,
    route_dependencies: List[Tuple[List[titiler.core.routing.EndpointScope], List[fastapi.params.Depends]]] = <factory>,
    extensions: List[titiler.core.factory.FactoryExtension] = <factory>,
    templates: starlette.templating.Jinja2Templates = <starlette.templating.Jinja2Templates object at 0x7f1b0d93cd10>,
    stats_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.StatisticsParams'>,
    histogram_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.HistogramParams'>,
    img_preview_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.PreviewParams'>,
    img_part_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.PartFeatureParams'>,
    tile_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.TileParams'>,
    add_preview: bool = True,
    add_part: bool = True,
    add_viewer: bool = True
)
```

Tiler Factory.

#### Attributes

| Name | Type | Description | Default |
|---|---|---|---|
| reader | rio_tiler.io.base.BaseReader | A rio-tiler reader. Defaults to `rio_tiler.io.Reader`. | `rio_tiler.io.Reader` |
| stats_dependency | titiler.core.dependencies.DefaultDependency | Endpoint dependency defining options for rio-tiler's statistics method. | None |
| histogram_dependency | titiler.core.dependencies.DefaultDependency | Endpoint dependency defining options for numpy's histogram method. | None |
| img_preview_dependency | titiler.core.dependencies.DefaultDependency | Endpoint dependency defining options for rio-tiler's preview method. | None |
| img_part_dependency | titiler.core.dependencies.DefaultDependency | Endpoint dependency defining options for rio-tiler's part/feature methods. | None |
| add_preview | bool | add `/preview` endpoints. Defaults to True. | True |
| add_part | bool | add `/bbox` and `/feature` endpoints. Defaults to True. | True |
| add_viewer | bool | add `/map` endpoints. Defaults to True. | True |

#### Ancestors (in MRO)

* titiler.core.factory.BaseTilerFactory

#### Descendants

* titiler.core.factory.MultiBaseTilerFactory
* titiler.core.factory.MultiBandTilerFactory

#### Class variables

```python3
add_part
```

```python3
add_preview
```

```python3
add_viewer
```

```python3
dataset_dependency
```

```python3
default_tms
```

```python3
histogram_dependency
```

```python3
img_part_dependency
```

```python3
img_preview_dependency
```

```python3
layer_dependency
```

```python3
reader
```

```python3
reader_dependency
```

```python3
render_dependency
```

```python3
router_prefix
```

```python3
stats_dependency
```

```python3
supported_tms
```

```python3
templates
```

```python3
tile_dependency
```

#### Methods

    
#### add_route_dependencies

```python3
def add_route_dependencies(
    self,
    *,
    scopes: List[titiler.core.routing.EndpointScope],
    dependencies=typing.List[fastapi.params.Depends]
)
```

Add dependencies to routes.

Allows a developer to add dependencies to a route after the route has been defined.

    
#### bounds

```python3
def bounds(
    self
)
```

Register /bounds endpoint.

    
#### color_formula_dependency

```python3
def color_formula_dependency(
    color_formula: Annotated[Optional[str], Query(PydanticUndefined)] = None
) -> Optional[str]
```

ColorFormula Parameter.

    
#### colormap_dependency

```python3
def colormap_dependency(
    colormap_name: Annotated[Literal['flag_r', 'gist_earth_r', 'cool', 'rdpu_r', 'matter_r', 'tempo_r', 'brbg', 'bwr_r', 'wistia', 'gist_yarg', 'ylgn', 'tarn_r', 'puor', 'purd', 'bupu', 'viridis_r', 'rdylbu_r', 'thermal_r', 'purples_r', 'gnuplot', 'winter', 'twilight_shifted_r', 'gnuplot_r', 'prism', 'viridis', 'pubugn_r', 'oxy', 'haline', 'ylorbr', 'winter_r', 'solar', 'gist_heat', 'rdylbu', 'dark2', 'dark2_r', 'terrain_r', 'set3', 'gray_r', 'tab20_r', 'brbg_r', 'rdylgn', 'twilight', 'balance_r', 'summer', 'hot', 'turbid', 'diff', 'speed', 'cmrmap', 'set3_r', 'pastel1', 'piyg_r', 'deep', 'greens_r', 'inferno_r', 'curl_r', 'pubugn', 'seismic_r', 'cmrmap_r', 'hsv_r', 'ylorrd', 'dense', 'oxy_r', 'bwr', 'bone', 'set1_r', 'pastel2', 'reds', 'delta_r', 'gist_rainbow_r', 'orrd_r', 'phase_r', 'pink', 'rainbow_r', 'set2_r', 'bugn', 'ocean', 'copper', 'gist_ncar', 'cubehelix', 'spring_r', 'cool_r', 'ocean_r', 'thermal', 'tab10_r', 'cividis', 'nipy_spectral', 'copper_r', 'inferno', 'amp_r', 'speed_r', 'tab10', 'gist_earth', 'prism_r', 'rdylgn_r', 'twilight_shifted', 'pubu', 'prgn_r', 'gist_gray', 'gray', 'pubu_r', 'purd_r', 'jet', 'flag', 'ice_r', 'tab20c_r', 'paired_r', 'cividis_r', 'gnbu_r', 'autumn_r', 'cfastie', 'spring', 'magma_r', 'rain_r', 'bugn_r', 'afmhot', 'pastel2_r', 'brg_r', 'puor_r', 'nipy_spectral_r', 'gist_stern', 'phase', 'deep_r', 'tempo', 'gist_ncar_r', 'amp', 'balance', 'spectral', 'cubehelix_r', 'delta', 'rain', 'diff_r', 'magma', 'greens', 'reds_r', 'gist_heat_r', 'piyg', 'set1', 'topo_r', 'bone_r', 'binary_r', 'tab20c', 'rdgy_r', 'wistia_r', 'topo', 'algae_r', 'autumn', 'gist_yarg_r', 'ylorrd_r', 'rdbu_r', 'pink_r', 'paired', 'matter', 'terrain', 'twilight_r', 'oranges', 'brg', 'ylgnbu_r', 'purples', 'set2', 'plasma', 'ylorbr_r', 'spectral_r', 'plasma_r', 'coolwarm', 'turbo_r', 'binary', 'schwarzwald', 'rdpu', 'greys_r', 'coolwarm_r', 'tarn', 'algae', 'oranges_r', 'rainbow', 'orrd', 'curl', 'accent', 'rplumbo', 'afmhot_r', 'turbo', 'hsv', 'ylgn_r', 'blues', 'tab20b', 'accent_r', 'ice', 'gist_stern_r', 'blues_r', 'rdbu', 'hot_r', 'jet_r', 'seismic', 'summer_r', 'ylgnbu', 'tab20b_r', 'pastel1_r', 'rdgy', 'gist_rainbow', 'dense_r', 'turbid_r', 'bupu_r', 'solar_r', 'gnbu', 'prgn', 'greys', 'tab20', 'haline_r', 'gist_gray_r', 'gnuplot2_r', 'gnuplot2'], Query(PydanticUndefined)] = None,
    colormap: Annotated[Optional[str], Query(PydanticUndefined)] = None
)
```

    
#### environment_dependency

```python3
def environment_dependency(
    
)
```

    
#### info

```python3
def info(
    self
)
```

Register /info endpoint.

    
#### map_viewer

```python3
def map_viewer(
    self
)
```

Register /map endpoint.

    
#### part

```python3
def part(
    self
)
```

Register /bbox and `/feature` endpoints.

    
#### path_dependency

```python3
def path_dependency(
    url: typing.Annotated[str, Query(PydanticUndefined)]
) -> str
```

Create dataset path from args

    
#### point

```python3
def point(
    self
)
```

Register /point endpoints.

    
#### preview

```python3
def preview(
    self
)
```

Register /preview endpoint.

    
#### process_dependency

```python3
def process_dependency(
    algorithm: Annotated[Literal['hillshade', 'contours', 'normalizedIndex', 'terrarium', 'terrainrgb'], Query(PydanticUndefined)] = None,
    algorithm_params: Annotated[Optional[str], Query(PydanticUndefined)] = None
) -> Optional[titiler.core.algorithm.base.BaseAlgorithm]
```

Data Post-Processing options.

    
#### register_routes

```python3
def register_routes(
    self
)
```

This Method register routes to the router.

Because we wrap the endpoints in a class we cannot define the routes as
methods (because of the self argument). The HACK is to define routes inside
the class method and register them after the class initialization.

    
#### rescale_dependency

```python3
def rescale_dependency(
    rescale: Annotated[Optional[List[str]], Query(PydanticUndefined)] = None
) -> Optional[List[Tuple[float, ...]]]
```

Min/Max data Rescaling

    
#### statistics

```python3
def statistics(
    self
)
```

add statistics endpoints.

    
#### tile

```python3
def tile(
    self
)
```

Register /tiles endpoint.

    
#### tilejson

```python3
def tilejson(
    self
)
```

Register /tilejson.json endpoint.

    
#### url_for

```python3
def url_for(
    self,
    request: starlette.requests.Request,
    name: str,
    **path_params: Any
) -> str
```

Return full url (with prefix) for a specific endpoint.

    
#### wmts

```python3
def wmts(
    self
)
```

Register /wmts endpoint.