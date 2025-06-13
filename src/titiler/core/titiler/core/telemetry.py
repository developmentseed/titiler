"""OpenTelemetry instrumentation for titiler.core."""

import functools
import inspect
from contextlib import contextmanager
from typing import Any, Awaitable, Callable, Dict, Iterator, Optional, TypeVar, overload

from typing_extensions import ParamSpec

from titiler.core import __version__

try:
    from opentelemetry import trace
    from opentelemetry.trace import Span, Status, StatusCode

    tracer = trace.get_tracer("titiler.core", __version__)

except ImportError:  # pragma: nocover
    # Create no-op versions of everything if OTel is not installed.
    trace = None
    Span = None
    Status = None
    StatusCode = None
    tracer = None

P = ParamSpec("P")
R = TypeVar("R")


class SpanWrapper:
    """A wrapper class to safely handle an optional OpenTelemetry Span."""

    # ... (this class remains unchanged) ...
    def __init__(self, span: Optional[Span]):
        """Set the span"""
        self._span = span

    def set_attributes(self, attributes: Dict[str, Any]) -> None:
        """Safely set attributes on the wrapped span if it exists."""
        if self._span:
            self._span.set_attributes(attributes)

    def record_exception(self, exception: Exception) -> None:
        """Safely record an exception on the wrapped span if it exists."""
        if self._span:
            self._span.record_exception(exception)


def _get_span_name(op_name: str, *args: Any) -> str:
    """Determine the span name based on the instance's prefix."""
    # ... (this function remains unchanged) ...
    if not args:
        return op_name

    instance = args[0]
    prefix = getattr(instance, "operation_prefix", "factory")
    return f"{prefix}.{op_name}"


def _extract_span_attributes(
    sig: inspect.Signature,
    custom_extractor: Optional[Callable[..., Dict[str, Any]]],
    *args: Any,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Extract span attributes using either a custom or automatic method."""
    # ... (this function remains unchanged) ...
    if custom_extractor:
        try:
            return custom_extractor(*args, **kwargs)
        except Exception:
            return {}

    # Default to automatic extraction
    try:
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        auto_attrs = {}
        for key, value in bound_args.arguments.items():
            if key in ("self", "request") or value is None:
                continue
            if hasattr(value, "value"):
                value = value.value
            if isinstance(value, (str, bool, int, float)):
                auto_attrs[f"titiler.path_param.{key}"] = value
        return auto_attrs
    except Exception:
        return {}


@contextmanager
def operation_tracer(
    operation_name: str,
    attributes: Optional[Dict[str, Any]] = None,
) -> Iterator[SpanWrapper]:
    """Context manager for tracing operations."""
    # ... (this function remains unchanged) ...
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
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


F = TypeVar("F", bound=Callable[..., Any])


@overload
def factory_trace(
    _func: Callable[P, Awaitable[R]],
) -> Callable[P, Awaitable[R]]: ...


@overload
def factory_trace(
    _func: Callable[P, R],
) -> Callable[P, R]: ...


@overload
def factory_trace(
    *,
    operation_name: Optional[str] = None,
    extract_attributes: Optional[Callable[..., Dict[str, Any]]] = None,
) -> Callable[[F], F]: ...


def factory_trace(
    _func: Optional[Callable[P, Any]] = None,
    *,
    operation_name: Optional[str] = None,
    extract_attributes: Optional[Callable[..., Dict[str, Any]]] = None,
) -> Any:
    """A decorator for Factory methods that automatically handles tracing."""

    def decorator(func: Callable[P, Any]) -> Callable[P, Any]:
        if not tracer:
            return func

        op_name = operation_name or func.__name__
        sig = inspect.signature(func)

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                span_name = _get_span_name(op_name, *args)
                attributes = _extract_span_attributes(
                    sig, extract_attributes, *args, **kwargs
                )
                with operation_tracer(span_name, attributes=attributes):
                    return await func(*args, **kwargs)

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                span_name = _get_span_name(op_name, *args)
                attributes = _extract_span_attributes(
                    sig, extract_attributes, *args, **kwargs
                )
                with operation_tracer(span_name, attributes=attributes):
                    return func(*args, **kwargs)

            return sync_wrapper

    if _func is None:
        return decorator
    else:
        return decorator(_func)


factory_trace.decorator_enabled = bool(tracer)  # type: ignore [attr-defined]
