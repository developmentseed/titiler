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
    pixel_selection: typing_extensions.Annotated[Literal['first', 'highest', 'lowest', 'mean', 'median', 'stdev', 'lastbandlow', 'lastbandhight', 'count'], Query(PydanticUndefined)] = 'first'
) -> rio_tiler.mosaic.methods.base.MosaicMethodBase
```

Returns the mosaic method used to combine datasets together.

## Classes

### MosaicTilerFactory

```python3
class MosaicTilerFactory(
    reader: Type[cogeo_mosaic.backends.base.BaseBackend] = <function MosaicBackend at 0x7fdcf3614d30>,
    router: fastapi.routing.APIRouter = <factory>,
    path_dependency: Callable[..., Any] = <function DatasetPathParams at 0x7fdcf2a0cdc0>,
    layer_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.BidxExprParams'>,
    dataset_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.DatasetParams'>,
    process_dependency: Callable[..., Union[titiler.core.algorithm.base.BaseAlgorithm, NoneType]] = <function Algorithms.dependency.<locals>.post_process at 0x7fdcf2780940>,
    rescale_dependency: Callable[..., Union[List[Tuple[float, ...]], NoneType]] = <function RescalingParams at 0x7fdcf2a0ce50>,
    color_formula_dependency: Callable[..., Union[str, NoneType]] = <function ColorFormulaParams at 0x7fdcf2991ca0>,
    colormap_dependency: Callable[..., Union[Dict[int, Tuple[int, int, int, int]], Sequence[Tuple[Tuple[Union[float, int], Union[float, int]], Tuple[int, int, int, int]]], NoneType]] = <function create_colormap_dependency.<locals>.deps at 0x7fdcf2a0cd30>,
    render_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.ImageRenderingParams'>,
    reader_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.DefaultDependency'>,
    environment_dependency: Callable[..., Dict] = <function BaseTilerFactory.<lambda> at 0x7fdcf27808b0>,
    supported_tms: morecantile.defaults.TileMatrixSets = TileMatrixSets(tms={'CDB1GlobalGrid': PosixPath('/opt/hostedtoolcache/Python/3.8.18/x64/lib/python3.8/site-packages/morecantile/data/CDB1GlobalGrid.json'), 'CanadianNAD83_LCC': PosixPath('/opt/hostedtoolcache/Python/3.8.18/x64/lib/python3.8/site-packages/morecantile/data/CanadianNAD83_LCC.json'), 'EuropeanETRS89_LAEAQuad': PosixPath('/opt/hostedtoolcache/Python/3.8.18/x64/lib/python3.8/site-packages/morecantile/data/EuropeanETRS89_LAEAQuad.json'), 'GNOSISGlobalGrid': PosixPath('/opt/hostedtoolcache/Python/3.8.18/x64/lib/python3.8/site-packages/morecantile/data/GNOSISGlobalGrid.json'), 'LINZAntarticaMapTilegrid': PosixPath('/opt/hostedtoolcache/Python/3.8.18/x64/lib/python3.8/site-packages/morecantile/data/LINZAntarticaMapTilegrid.json'), 'NZTM2000Quad': PosixPath('/opt/hostedtoolcache/Python/3.8.18/x64/lib/python3.8/site-packages/morecantile/data/NZTM2000Quad.json'), 'UPSAntarcticWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.8.18/x64/lib/python3.8/site-packages/morecantile/data/UPSAntarcticWGS84Quad.json'), 'UPSArcticWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.8.18/x64/lib/python3.8/site-packages/morecantile/data/UPSArcticWGS84Quad.json'), 'UTM31WGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.8.18/x64/lib/python3.8/site-packages/morecantile/data/UTM31WGS84Quad.json'), 'WGS1984Quad': PosixPath('/opt/hostedtoolcache/Python/3.8.18/x64/lib/python3.8/site-packages/morecantile/data/WGS1984Quad.json'), 'WebMercatorQuad': <TileMatrixSet title='Google Maps Compatible for the World' id='WebMercatorQuad' crs='http://www.opengis.net/def/crs/EPSG/0/3857>, 'WorldCRS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.8.18/x64/lib/python3.8/site-packages/morecantile/data/WorldCRS84Quad.json'), 'WorldMercatorWGS84Quad': PosixPath('/opt/hostedtoolcache/Python/3.8.18/x64/lib/python3.8/site-packages/morecantile/data/WorldMercatorWGS84Quad.json')}),
    default_tms: Union[str, NoneType] = None,
    router_prefix: str = '',
    optional_headers: List[titiler.core.resources.enums.OptionalHeader] = <factory>,
    route_dependencies: List[Tuple[List[titiler.core.routing.EndpointScope], List[fastapi.params.Depends]]] = <factory>,
    extensions: List[titiler.core.factory.FactoryExtension] = <factory>,
    templates: starlette.templating.Jinja2Templates = <starlette.templating.Jinja2Templates object at 0x7fdcf27aa910>,
    dataset_reader: Union[Type[rio_tiler.io.base.BaseReader], Type[rio_tiler.io.base.MultiBaseReader], Type[rio_tiler.io.base.MultiBandReader]] = <class 'rio_tiler.io.rasterio.Reader'>,
    backend_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.DefaultDependency'>,
    pixel_selection_dependency: Callable[..., rio_tiler.mosaic.methods.base.MosaicMethodBase] = <function PixelSelectionParams at 0x7fdcf3614c10>,
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
    color_formula: typing_extensions.Annotated[Union[str, NoneType], Query(PydanticUndefined)] = None
) -> Union[str, NoneType]
```

ColorFormula Parameter.

    
#### colormap_dependency

```python3
def colormap_dependency(
    colormap_name: typing_extensions.Annotated[Literal['rdbu', 'turbid_r', 'bone_r', 'orrd_r', 'tempo', 'pubu', 'summer', 'gist_gray', 'cmrmap_r', 'rdgy', 'greens', 'hsv_r', 'gnuplot_r', 'nipy_spectral_r', 'purd', 'accent_r', 'paired', 'spring', 'tab20_r', 'speed', 'oxy_r', 'plasma_r', 'tarn', 'terrain_r', 'inferno', 'ylgn', 'ice_r', 'tab20b_r', 'prism_r', 'diff', 'twilight_r', 'afmhot_r', 'oranges', 'speed_r', 'delta_r', 'deep_r', 'spectral_r', 'gnbu', 'thermal_r', 'jet', 'rplumbo', 'gist_earth', 'ice', 'gist_gray_r', 'set1_r', 'rainbow_r', 'brbg', 'turbo_r', 'orrd', 'solar', 'pastel1', 'reds_r', 'balance_r', 'piyg_r', 'rain_r', 'pubugn_r', 'ocean', 'algae_r', 'magma', 'tempo_r', 'rdpu', 'brg', 'bone', 'jet_r', 'binary_r', 'pink', 'rdylgn', 'piyg', 'turbo', 'dark2_r', 'algae', 'gray', 'hot', 'ylgn_r', 'paired_r', 'set3', 'ylorbr_r', 'brg_r', 'pubugn', 'blues_r', 'rdylbu', 'pubu_r', 'nipy_spectral', 'matter', 'tab20b', 'bupu_r', 'haline_r', 'tab20c', 'ylgnbu', 'bugn', 'solar_r', 'delta', 'cmrmap', 'binary', 'autumn_r', 'coolwarm', 'autumn', 'bupu', 'gnbu_r', 'pastel1_r', 'copper', 'wistia_r', 'tab20c_r', 'seismic', 'gist_stern_r', 'tab10', 'copper_r', 'accent', 'cividis_r', 'gist_ncar', 'gist_ncar_r', 'ylorbr', 'topo', 'balance', 'winter_r', 'gist_heat_r', 'ylgnbu_r', 'brbg_r', 'dense_r', 'gray_r', 'rdylbu_r', 'set2', 'gist_yarg', 'inferno_r', 'cool_r', 'prgn', 'gist_stern', 'pink_r', 'blues', 'greys_r', 'terrain', 'oranges_r', 'cubehelix', 'pastel2', 'greys', 'spectral', 'gist_heat', 'ylorrd', 'tarn_r', 'gist_rainbow', 'prism', 'greens_r', 'rain', 'hot_r', 'winter', 'amp', 'gnuplot', 'deep', 'ylorrd_r', 'amp_r', 'rdylgn_r', 'twilight_shifted', 'oxy', 'gist_earth_r', 'puor_r', 'twilight', 'purd_r', 'puor', 'thermal', 'haline', 'wistia', 'purples_r', 'rdgy_r', 'gist_rainbow_r', 'gnuplot2', 'viridis_r', 'ocean_r', 'set1', 'gist_yarg_r', 'dense', 'rdbu_r', 'flag', 'set3_r', 'plasma', 'twilight_shifted_r', 'turbid', 'phase_r', 'matter_r', 'bwr_r', 'tab10_r', 'diff_r', 'bwr', 'curl', 'afmhot', 'schwarzwald', 'reds', 'topo_r', 'magma_r', 'set2_r', 'pastel2_r', 'dark2', 'hsv', 'phase', 'spring_r', 'flag_r', 'coolwarm_r', 'cubehelix_r', 'cividis', 'purples', 'cool', 'gnuplot2_r', 'seismic_r', 'summer_r', 'prgn_r', 'cfastie', 'curl_r', 'viridis', 'bugn_r', 'rdpu_r', 'rainbow', 'tab20'], Query(PydanticUndefined)] = None,
    colormap: typing_extensions.Annotated[Union[str, NoneType], Query(PydanticUndefined)] = None
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
    url: typing_extensions.Annotated[str, Query(PydanticUndefined)]
) -> str
```

Create dataset path from args

    
#### pixel_selection_dependency

```python3
def pixel_selection_dependency(
    pixel_selection: typing_extensions.Annotated[Literal['first', 'highest', 'lowest', 'mean', 'median', 'stdev', 'lastbandlow', 'lastbandhight', 'count'], Query(PydanticUndefined)] = 'first'
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
    algorithm: typing_extensions.Annotated[Literal['hillshade', 'contours', 'normalizedIndex', 'terrarium', 'terrainrgb'], Query(PydanticUndefined)] = None,
    algorithm_params: typing_extensions.Annotated[Union[str, NoneType], Query(PydanticUndefined)] = None
) -> Union[titiler.core.algorithm.base.BaseAlgorithm, NoneType]
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
    rescale: typing_extensions.Annotated[Union[List[str], NoneType], Query(PydanticUndefined)] = None
) -> Union[List[Tuple[float, ...]], NoneType]
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