"""OpenTelemetry instrumentation for titiler.core."""

import functools
import sys  # <--- Import the sys module
from contextlib import contextmanager
from typing import Any, Callable, Dict, Iterator, Optional, TypeVar

if sys.version_info >= (3, 10):
    from typing import ParamSpec
else:
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


def trace_method(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to trace a method with OpenTelemetry."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        if not tracer:
            return func

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            span_name = name or f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    span.set_attributes(attributes)

                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        return wrapper

    return decorator


def trace_factory_method(
    operation_type: str,
    extract_attributes: Optional[Callable[P, Dict[str, Any]]] = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Specialized decorator for factory methods."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        if not tracer:
            return func

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            span_name = f"titiler.{operation_type}"

            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("titiler.operation", operation_type)

                if extract_attributes:
                    try:
                        attrs = extract_attributes(*args, **kwargs)
                        span.set_attributes(attrs)
                    except Exception:
                        # Silently passing is reasonable here if attribute
                        # extraction is non-critical.
                        pass

                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        return wrapper

    return decorator


@contextmanager
def trace_operation(
    operation_name: str,
    attributes: Optional[Dict[str, Any]] = None,
) -> Iterator[Optional[Span]]:
    """Context manager for tracing operations."""
    if not tracer:
        yield None
        return

    with tracer.start_as_current_span(operation_name) as span:
        if attributes:
            span.set_attributes(attributes)

        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise
