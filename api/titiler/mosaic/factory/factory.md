# Module titiler.mosaic.factory

TiTiler.mosaic Router factories.

## Variables

```python3
MAX_THREADS
```

```python3
WGS84_CRS
```

```python3
img_endpoint_params
```

## Functions

    
### PixelSelectionParams

```python3
def PixelSelectionParams(
    pixel_selection: Annotated[Literal['first', 'highest', 'lowest', 'mean', 'median', 'stdev', 'lastbandlow', 'lastbandhight', 'count'], Query(PydanticUndefined)] = 'first'
) -> rio_tiler.mosaic.methods.base.MosaicMethodBase
```

Returns the mosaic method used to combine datasets together.

## Classes

### MosaicTilerFactory

```python3
class MosaicTilerFactory(
    reader: Type[cogeo_mosaic.backends.base.BaseBackend] = <function MosaicBackend at 0x7fbf45522340>,
    router: fastapi.routing.APIRouter = <factory>,
    path_dependency: Callable[..., Any] = <function DatasetPathParams at 0x7fbf44b10400>,
    layer_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.BidxExprParams'>,
    dataset_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.DatasetParams'>,
    process_dependency: Callable[..., Optional[titiler.core.algorithm.base.BaseAlgorithm]] = <function Algorithms.dependency.<locals>.post_process at 0x7fbf44911e40>,
    rescale_dependency: Callable[..., Optional[List[Tuple[float, ...]]]] = <function RescalingParams at 0x7fbf44b113a0>,
    color_formula_dependency: Callable[..., Optional[str]] = <function ColorFormulaParams at 0x7fbf44b740e0>,
    colormap_dependency: Callable[..., Union[Dict[int, Tuple[int, int, int, int]], Sequence[Tuple[Tuple[Union[float, int], Union[float, int]], Tuple[int, int, int, int]]], NoneType]] = <function create_colormap_dependency.<locals>.deps at 0x7fbf44b10360>,
    render_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.ImageRenderingParams'>,
    reader_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.DefaultDependency'>,
    environment_dependency: Callable[..., Dict] = <function BaseTilerFactory.<lambda> at 0x7fbf44911ee0>,
    supported_tms: morecantile.defaults.TileMatrixSets = TileMatrixSets(tms={'CDB1GlobalGrid': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/CDB1GlobalGrid.json'), 'CanadianNAD83_LCC': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/CanadianNAD83_LCC.json'), 'EuropeanETRS89_LAEAQuad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/EuropeanETRS89_LAEAQuad.json'), 'GNOSISGlobalGrid': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/GNOSISGlobalGrid.json'), 'LINZAntarticaMapTilegrid': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/LINZAntarticaMapTilegrid.json'), 'NZTM2000Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/NZTM2000Quad.json'), 'UPSAntarcticWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/UPSAntarcticWGS84Quad.json'), 'UPSArcticWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/UPSArcticWGS84Quad.json'), 'UTM31WGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/UTM31WGS84Quad.json'), 'WGS1984Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/WGS1984Quad.json'), 'WebMercatorQuad': <TileMatrixSet title='Google Maps Compatible for the World' id='WebMercatorQuad' crs='http://www.opengis.net/def/crs/EPSG/0/3857>, 'WorldCRS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/WorldCRS84Quad.json'), 'WorldMercatorWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/morecantile/data/WorldMercatorWGS84Quad.json')}),
    default_tms: Optional[str] = None,
    router_prefix: str = '',
    optional_headers: List[titiler.core.resources.enums.OptionalHeader] = <factory>,
    route_dependencies: List[Tuple[List[titiler.core.routing.EndpointScope], List[fastapi.params.Depends]]] = <factory>,
    extensions: List[titiler.core.factory.FactoryExtension] = <factory>,
    templates: starlette.templating.Jinja2Templates = <starlette.templating.Jinja2Templates object at 0x7fbf44aab110>,
    dataset_reader: Union[Type[rio_tiler.io.base.BaseReader], Type[rio_tiler.io.base.MultiBaseReader], Type[rio_tiler.io.base.MultiBandReader]] = <class 'rio_tiler.io.rasterio.Reader'>,
    backend_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.DefaultDependency'>,
    pixel_selection_dependency: Callable[..., rio_tiler.mosaic.methods.base.MosaicMethodBase] = <function PixelSelectionParams at 0x7fbf4f528c20>,
    tile_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.TileParams'>,
    add_viewer: bool = True
)
```

MosaicTiler Factory.

The main difference with titiler.endpoint.factory.TilerFactory is that this factory
needs the `reader` to be of `cogeo_mosaic.backends.BaseBackend` type (e.g MosaicBackend) and a `dataset_reader` (BaseReader).

#### Ancestors (in MRO)

* titiler.core.factory.BaseTilerFactory

#### Class variables

```python3
add_viewer
```

```python3
backend_dependency
```

```python3
dataset_dependency
```

```python3
dataset_reader
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

    
#### assets

```python3
def assets(
    self
)
```

Register /assets endpoint.

    
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

Register /info endpoint

    
#### map_viewer

```python3
def map_viewer(
    self
)
```

Register /map endpoint.

    
#### path_dependency

```python3
def path_dependency(
    url: typing.Annotated[str, Query(PydanticUndefined)]
) -> str
```

Create dataset path from args

    
#### pixel_selection_dependency

```python3
def pixel_selection_dependency(
    pixel_selection: Annotated[Literal['first', 'highest', 'lowest', 'mean', 'median', 'stdev', 'lastbandlow', 'lastbandhight', 'count'], Query(PydanticUndefined)] = 'first'
) -> rio_tiler.mosaic.methods.base.MosaicMethodBase
```

Returns the mosaic method used to combine datasets together.

    
#### point

```python3
def point(
    self
)
```

Register /point endpoint.

    
#### process_dependency

```python3
def process_dependency(
    algorithm: Annotated[Literal['hillshade', 'contours', 'normalizedIndex', 'terrarium', 'terrainrgb'], Query(PydanticUndefined)] = None,
    algorithm_params: Annotated[Optional[str], Query(PydanticUndefined)] = None
) -> Optional[titiler.core.algorithm.base.BaseAlgorithm]
```

Data Post-Processing options.

    
#### read

```python3
def read(
    self
)
```

Register / (Get) Read endpoint.

    
#### reader

```python3
def reader(
    input: str,
    *args: Any,
    **kwargs: Any
) -> cogeo_mosaic.backends.base.BaseBackend
```

Select mosaic backend for input.

    
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

    
#### tile

```python3
def tile(
    self
)
```

Register /tiles endpoints.

    
#### tilejson

```python3
def tilejson(
    self
)
```

Add tilejson endpoint.

    
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

    
#### validate

```python3
def validate(
    self
)
```

Register /validate endpoint.

    
#### wmts

```python3
def wmts(
    self
)
```

Add wmts endpoint.