# Module titiler.core.routing

Custom routing classes.

None

## Functions

    
### apiroute_factory

```python3
def apiroute_factory(
    env: Union[Dict, NoneType] = None
) -> Type[fastapi.routing.APIRoute]
```

    
Create Custom API Route class with custom Env.

Because we cannot create middleware for specific router we need to create
a custom APIRoute which add the `rasterio.Env(` block before the endpoint is
actually called. This way we set the env outside the threads and we make sure
that event multithreaded Reader will get the environment set.

Note: This has been tested in python 3.6 and 3.7 only.