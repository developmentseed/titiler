# Module titiler.core.errors

Titiler error classes.

None

## Variables

```python3
DEFAULT_STATUS_CODES
```

```python3
logger
```

## Functions

    
### add_exception_handlers

```python3
def add_exception_handlers(
    app: fastapi.applications.FastAPI,
    status_codes: Dict[Type[Exception], int]
) -> None
```

    
Add exception handlers to the FastAPI app.

    
### exception_handler_factory

```python3
def exception_handler_factory(
    status_code: int
) -> Callable
```

    
Create a FastAPI exception handler from a status code.

## Classes

### BadRequestError

```python3
class BadRequestError(
    /,
    *args,
    **kwargs
)
```

#### Ancestors (in MRO)

* titiler.core.errors.TilerError
* builtins.Exception
* builtins.BaseException

#### Class variables

```python3
args
```

#### Methods

    
#### with_traceback

```python3
def with_traceback(
    ...
)
```

    
Exception.with_traceback(tb) --

set self.__traceback__ to tb and return self.

### TileNotFoundError

```python3
class TileNotFoundError(
    /,
    *args,
    **kwargs
)
```

#### Ancestors (in MRO)

* titiler.core.errors.TilerError
* builtins.Exception
* builtins.BaseException

#### Class variables

```python3
args
```

#### Methods

    
#### with_traceback

```python3
def with_traceback(
    ...
)
```

    
Exception.with_traceback(tb) --

set self.__traceback__ to tb and return self.

### TilerError

```python3
class TilerError(
    /,
    *args,
    **kwargs
)
```

#### Ancestors (in MRO)

* builtins.Exception
* builtins.BaseException

#### Descendants

* titiler.core.errors.TileNotFoundError
* titiler.core.errors.BadRequestError

#### Class variables

```python3
args
```

#### Methods

    
#### with_traceback

```python3
def with_traceback(
    ...
)
```

    
Exception.with_traceback(tb) --

set self.__traceback__ to tb and return self.