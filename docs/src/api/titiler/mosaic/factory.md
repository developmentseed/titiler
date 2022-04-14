# Module titiler.mosaic.factory

TiTiler.mosaic Router factories.

None

## Variables

```python3
MAX_THREADS
```

```python3
img_endpoint_params
```

## Classes

### MosaicTilerFactory

```python3
class MosaicTilerFactory(
    reader: Type[cogeo_mosaic.backends.base.BaseBackend] = <function MosaicBackend at 0x1396f40d0>,
    reader_options: Dict = <factory>,
    router: fastapi.routing.APIRouter = <factory>,
    path_dependency: Callable[..., str] = <function DatasetPathParams at 0x139dd9550>,
    dataset_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.DatasetParams'>,
    layer_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.BidxExprParams'>,
    render_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.ImageRenderingParams'>,
    colormap_dependency: Callable[..., Union[Dict, NoneType]] = <function ColorMapParams at 0x139dd94c0>,
    process_dependency: Type[titiler.core.dependencies.DefaultDependency] = <class 'titiler.core.dependencies.PostProcessParams'>,
    tms_dependency: Callable[..., morecantile.models.TileMatrixSet] = <function WebMercatorTMSParams at 0x1398e6940>,
    additional_dependency: Callable[..., Dict] = <function BaseTilerFactory.<lambda> at 0x139f0aa60>,
    router_prefix: str = '',
    gdal_config: Dict = <factory>,
    optional_headers: List[titiler.core.resources.enums.OptionalHeader] = <factory>,
    dataset_reader: Type[rio_tiler.io.base.BaseReader] = <class 'rio_tiler.io.cogeo.COGReader'>,
    backend_options: Dict = <factory>
)
```

#### Ancestors (in MRO)

* titiler.core.factory.BaseTilerFactory

#### Class variables

```python3
dataset_dependency
```

```python3
dataset_reader
```

```python3
layer_dependency
```

```python3
process_dependency
```

```python3
render_dependency
```

```python3
router_prefix
```

#### Methods

    
#### additional_dependency

```python3
def additional_dependency(
    
)
```

    

    
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

    
#### colormap_dependency

```python3
def colormap_dependency(
    colormap_name: titiler.core.dependencies.ColorMapName = Query(None),
    colormap: str = Query(None)
) -> Union[Dict, Sequence, NoneType]
```

    
Colormap Dependency.

    
#### info

```python3
def info(
    self
)
```

    
Register /info endpoint

    
#### path_dependency

```python3
def path_dependency(
    url: str = Query(Ellipsis)
) -> str
```

    
Create dataset path from args

    
#### point

```python3
def point(
    self
)
```

    
Register /point endpoint.

    
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
    url: str,
    *args: Any,
    **kwargs: Any
) -> cogeo_mosaic.backends.base.BaseBackend
```

    
Select mosaic backend for url.

    
#### register_routes

```python3
def register_routes(
    self
)
```

    
This Method register routes to the router.

Because we wrap the endpoints in a class we cannot define the routes as
methods (because of the self argument). The HACK is to define routes inside
the class method and register them after the class initialisation.

    
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

    
#### tms_dependency

```python3
def tms_dependency(
    TileMatrixSetId: titiler.core.dependencies.WebMercatorTileMatrixSetName = Query(WebMercatorTileMatrixSetName.WebMercatorQuad)
) -> morecantile.models.TileMatrixSet
```

    
TileMatrixSet Dependency.

    
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