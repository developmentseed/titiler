# Module titiler.core.routing

Custom routing classes.

## Functions

    
### add_route_dependencies

```python3
def add_route_dependencies(
    routes: List[starlette.routing.BaseRoute],
    *,
    scopes: List[titiler.core.routing.EndpointScope],
    dependencies=typing.List[fastapi.params.Depends]
)
```

Add dependencies to routes.

Allows a developer to add dependencies to a route after the route has been defined.

    
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

## Classes

### EndpointScope

```python3
class EndpointScope(
    /,
    *args,
    **kwargs
)
```

Define endpoint.

#### Ancestors (in MRO)

* builtins.dict

#### Methods

    
#### clear

```python3
def clear(
    ...
)
```

D.clear() -> None.  Remove all items from D.

    
#### copy

```python3
def copy(
    ...
)
```

D.copy() -> a shallow copy of D

    
#### fromkeys

```python3
def fromkeys(
    iterable,
    value=None,
    /
)
```

Create a new dictionary with keys from iterable and values set to value.

    
#### get

```python3
def get(
    self,
    key,
    default=None,
    /
)
```

Return the value for key if key is in the dictionary, else default.

    
#### items

```python3
def items(
    ...
)
```

D.items() -> a set-like object providing a view on D's items

    
#### keys

```python3
def keys(
    ...
)
```

D.keys() -> a set-like object providing a view on D's keys

    
#### pop

```python3
def pop(
    ...
)
```

D.pop(k[,d]) -> v, remove specified key and return the corresponding value.

If key is not found, d is returned if given, otherwise KeyError is raised

    
#### popitem

```python3
def popitem(
    self,
    /
)
```

Remove and return a (key, value) pair as a 2-tuple.

Pairs are returned in LIFO (last-in, first-out) order.
Raises KeyError if the dict is empty.

    
#### setdefault

```python3
def setdefault(
    self,
    key,
    default=None,
    /
)
```

Insert key with a value of default if key is not in the dictionary.

Return the value for key if key is in the dictionary, else default.

    
#### update

```python3
def update(
    ...
)
```

D.update([E, ]**F) -> None.  Update D from dict/iterable E and F.

If E is present and has a .keys() method, then does:  for k in E: D[k] = E[k]
If E is present and lacks a .keys() method, then does:  for k, v in E: D[k] = v
In either case, this is followed by: for k in F:  D[k] = F[k]

    
#### values

```python3
def values(
    ...
)
```

D.values() -> an object providing a view on D's values