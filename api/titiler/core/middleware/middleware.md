# Module titiler.core.middleware

Titiler middlewares.

## Classes

### CacheControlMiddleware

```python3
class CacheControlMiddleware(
    app: Callable[[MutableMapping[str, Any], Callable[[], Awaitable[MutableMapping[str, Any]]], Callable[[MutableMapping[str, Any]], Awaitable[NoneType]]], Awaitable[NoneType]],
    cachecontrol: Union[str, NoneType] = None,
    cachecontrol_max_http_code: Union[int, NoneType] = 500,
    exclude_path: Union[Set[str], NoneType] = None
)
```

MiddleWare to add CacheControl in response headers.

### LoggerMiddleware

```python3
class LoggerMiddleware(
    app: Callable[[MutableMapping[str, Any], Callable[[], Awaitable[MutableMapping[str, Any]]], Callable[[MutableMapping[str, Any]], Awaitable[NoneType]]], Awaitable[NoneType]],
    querystrings: bool = False,
    headers: bool = False
)
```

MiddleWare to add logging.

### LowerCaseQueryStringMiddleware

```python3
class LowerCaseQueryStringMiddleware(
    app: Callable[[MutableMapping[str, Any], Callable[[], Awaitable[MutableMapping[str, Any]]], Callable[[MutableMapping[str, Any]], Awaitable[NoneType]]], Awaitable[NoneType]]
)
```

Middleware to make URL parameters case-insensitive.

taken from: https://github.com/tiangolo/fastapi/issues/826

### TotalTimeMiddleware

```python3
class TotalTimeMiddleware(
    app: Callable[[MutableMapping[str, Any], Callable[[], Awaitable[MutableMapping[str, Any]]], Callable[[MutableMapping[str, Any]], Awaitable[NoneType]]], Awaitable[NoneType]]
)
```

MiddleWare to add Total process time in response headers.