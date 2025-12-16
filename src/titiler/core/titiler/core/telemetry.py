"""OpenTelemetry instrumentation for titiler.core."""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any, Iterator, ParamSpec, TypeVar

from titiler.core import __version__

try:
    from opentelemetry import trace
    from opentelemetry.trace import Span, Status, StatusCode

    tracer = trace.get_tracer("titiler.core", __version__)
except ImportError:
    trace = None  # type: ignore
    Span = None  # type: ignore
    Status = None  # type: ignore
    StatusCode = None  # type: ignore
    tracer = None  # type: ignore

P = ParamSpec("P")
R = TypeVar("R")


def add_span_attributes(attributes: dict[str, Any]) -> None:
    """Adds attributes to the current active span."""
    if not tracer:
        return
    span = trace.get_current_span()
    if span and span.is_recording():
        span.set_attributes(attributes)


def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """Flattens a nested dictionary for adding span attributes."""
    items = {}
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            if not isinstance(v, (str, bool, int, float)):
                v = str(v)
            items[new_key] = v
    return items


class SpanWrapper:
    """A wrapper class to safely handle an optional OpenTelemetry Span."""

    def __init__(self, span: Span | None):
        """Set the span"""
        self._span = span

    def set_attributes(self, attributes: dict[str, Any]) -> None:
        """Safely set attributes on the wrapped span if it exists."""
        if self._span:
            self._span.set_attributes(attributes)

    def record_exception(self, exception: Exception) -> None:
        """Safely record an exception on the wrapped span if it exists."""
        if self._span:
            self._span.record_exception(exception)


@contextmanager
def operation_tracer(
    operation_name: str,
    attributes: dict[str, Any] | None = None,
) -> Iterator[SpanWrapper]:
    """Context manager for creating granular child spans."""
    if not tracer:
        yield SpanWrapper(None)
        return

    with tracer.start_as_current_span(operation_name) as span:
        wrapped_span = SpanWrapper(span)
        if attributes:
            wrapped_span.set_attributes(attributes)
        try:
            yield wrapped_span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


def _get_span_name(op_name: str, factory_instance: Any) -> str:
    """Determine the span name using the factory class name."""
    if not factory_instance:
        return op_name
    class_name = factory_instance.__class__.__name__
    return f"{class_name}.{op_name}"


def factory_trace(
    _func: Callable[P, Any] | None = None,
    *,
    factory_instance: Any | None = None,
) -> Any:
    """A decorator for Factory methods that automatically handles tracing for factory methods"""

    def decorator(func: Callable[P, Any]) -> Callable[P, Any]:
        if not tracer:
            return func

        op_name = func.__name__

        attributes = {}
        if factory_instance:
            if hasattr(factory_instance, "reader"):
                attributes["reader"] = str(factory_instance.reader)
            if hasattr(factory_instance, "backend"):
                attributes["backend"] = str(factory_instance.backend)

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                span_name = _get_span_name(op_name, factory_instance)
                with operation_tracer(span_name, attributes=attributes):
                    return await func(*args, **kwargs)

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                span_name = _get_span_name(op_name, factory_instance)
                with operation_tracer(span_name, attributes=attributes):
                    return func(*args, **kwargs)

            return sync_wrapper

    return decorator if _func is None else decorator(_func)


factory_trace.decorator_enabled = bool(tracer)  # type: ignore [attr-defined]
