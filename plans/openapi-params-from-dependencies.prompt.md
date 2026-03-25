# OpenAPI schema from FastAPI dependencies

## Problem

In the WMTS extension, we construct an endpoint which can accept query-parameter or use `render` configuration to inject them as tile layers. Because the tile's dependencies are not part of the endpoint function signature, so FastAPI won't include them in the OpenAPI schema automatically. This means they won't be documented in the interactive API docs or available for client code generation.

We then need to manually extract the query parameter definitions from a set of dependencies and add them to the OpenAPI schema for the endpoint.

See issue [#1345](https://github.com/developmentseed/titiler/issues/1345)

## Utility function

Add to your utils module:

```python
from fastapi._compat import get_definitions, get_flat_models_from_fields, get_model_name_map
from fastapi.dependencies.models import Dependant
from fastapi.dependencies.utils import get_dependant, get_flat_params
from fastapi.openapi.utils import _get_openapi_operation_parameters

def dependencies_to_openapi_params(
    dependencies: list[Callable],
) -> list[dict[str, Any]]:
    """Extract OpenAPI query parameter schemas from a list of FastAPI dependencies."""
    all_fields = []
    seen: set[str] = set()
    for dep in dependencies:
        dependant = get_dependant(path="", call=dep)
        for field in get_flat_params(dependant):
            if field.name not in seen:
                seen.add(field.name)
                all_fields.append(field)

    if not all_fields:
        return []

    flat_models = get_flat_models_from_fields(all_fields, known_models=set())
    model_name_map = get_model_name_map(flat_models)
    field_mapping, _ = get_definitions(fields=all_fields, model_name_map=model_name_map)

    combined = Dependant(path="")
    combined.query_params = all_fields
    return _get_openapi_operation_parameters(
        dependant=combined,
        model_name_map=model_name_map,
        field_mapping=field_mapping,
    )
```

## Usage in a route

Pass the result to `openapi_extra` in the route decorator:

```python
@router.get(
    "/some-endpoint",
    openapi_extra={
        "parameters": dependencies_to_openapi_params(my_dependencies),
    },
)
def my_endpoint(...):
    ...
```

## Implementation plan

1. **Add utility to `titiler/core/titiler/core/utils.py`**
   - Add imports: `get_definitions`, `get_flat_models_from_fields`, `get_model_name_map` from `fastapi._compat`; `Dependant` from `fastapi.dependencies.models`; `get_flat_params` from `fastapi.dependencies.utils`; `_get_openapi_operation_parameters` from `fastapi.openapi.utils`
   - Add the `dependencies_to_openapi_params` function (see above)
   - Export it from `titiler.core.utils`

2. **Use in the extension route** (e.g. `titiler/extensions/titiler/extensions/wmts.py`)
   - Import `dependencies_to_openapi_params` from `titiler.core.utils`
   - Before registering the route, build the list of `tile_dependencies`
   - Pass `"parameters": dependencies_to_openapi_params(tile_dependencies)` to `openapi_extra` on the `@router.get(...)` decorator

3. **Tests**
   - In `titiler/core/tests/test_utils.py`: add `test_dependencies_to_openapi_params` covering empty list, single dep, multiple deps merged, `required` flag, and deduplication

## Notes

- Parameters are deduplicated by name across all dependencies.
- `required`, `schema`, and `description` are derived from the `Query(...)` annotations on each dependency.
- This uses FastAPI internals (`_get_openapi_operation_parameters`, `_compat`) — tested against FastAPI 0.135+.
