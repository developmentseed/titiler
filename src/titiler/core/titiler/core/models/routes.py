"""models for routes."""

from typing import Optional, TypedDict


class EndpointScope(TypedDict, total=False):
    """Define endpoint."""

    # More strict version of Starlette's Scope
    # https://github.com/encode/starlette/blob/6af5c515e0a896cbf3f86ee043b88f6c24200bcf/starlette/types.py#L3
    path: str
    method: str
    type: Optional[str]  # http or websocket
