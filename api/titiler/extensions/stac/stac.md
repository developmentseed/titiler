# Module titiler.extensions.stac

rio-stac Extension.

## Classes

### Item

```python3
class Item(
    /,
    *args,
    **kwargs
)
```

STAC Item.

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

### stacExtension

```python3
class stacExtension(
    
)
```

Add /stac endpoint to a COG TilerFactory.

#### Ancestors (in MRO)

* titiler.core.factory.FactoryExtension

#### Methods

    
#### register

```python3
def register(
    self,
    factory: titiler.core.factory.BaseTilerFactory
)
```

Register endpoint to the tiler factory.