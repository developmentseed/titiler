"""Optional Prometheus HTTP metrics for titiler.core.

App-level instrumentation complementary to OpenTelemetry factory telemetry.
Install with ``pip install titiler.core[metrics]``.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastapi import FastAPI
    from prometheus_client import CollectorRegistry
    from prometheus_fastapi_instrumentator.metrics import Info

try:
    from prometheus_client import REGISTRY, Counter, Histogram
    from prometheus_fastapi_instrumentator import Instrumentator

    metrics_available = True
except ImportError:  # pragma: no cover
    REGISTRY = None  # type: ignore[assignment]
    Counter = None  # type: ignore[assignment, misc]
    Histogram = None  # type: ignore[assignment, misc]
    Instrumentator = None  # type: ignore[assignment, misc]
    metrics_available = False

OperationResolver = Callable[["Info"], str]

_STATE_KEY = "titiler_metrics_instrumentator"

# Reuse collectors across apps that share a registry + metric prefix.
_COLLECTORS: dict[tuple[int, str], tuple[Any, Any]] = {}

_DEFAULT_LATENCY_BUCKETS = (
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
    float("inf"),
)


def _missing_metrics_extra() -> ImportError:
    """Build the install hint raised when the metrics extra is missing."""
    return ImportError(
        "Prometheus metrics require the [metrics] extra. "
        "Install with: pip install 'titiler.core[metrics]'"
    )


def _exclude_pattern(path: str) -> str:
    """Build an exclusion regex that matches ``path`` with an optional trailing slash."""
    return rf"^{re.escape(path.rstrip('/'))}/?$"


def get_route_path(info: Info) -> str | None:
    """Return the templated route path for a request, if available."""
    route = info.request.scope.get("route")
    if route is None:
        return None
    return getattr(route, "path", None)


def default_operation_resolver(info: Info) -> str:
    """Resolve a low-cardinality operation label from route metadata.

    Preference order:
    1. FastAPI ``operation_id``
    2. Route ``name``
    3. Templated route ``path``
    4. Instrumentator ``modified_handler``
    5. ``"unknown"``
    """
    route = info.request.scope.get("route")
    if route is not None:
        operation_id = getattr(route, "operation_id", None)
        if operation_id:
            return operation_id

        name = getattr(route, "name", None)
        if name:
            return name

        path = getattr(route, "path", None)
        if path:
            return path

    handler = getattr(info, "modified_handler", None)
    if handler and handler != "none":
        return handler

    return "unknown"


def _get_or_create_collectors(
    *,
    metric_prefix: str,
    registry: CollectorRegistry,
    latency_buckets: Sequence[float],
) -> tuple[Any, Any]:
    """Return shared request/latency collectors for a registry + prefix."""
    key = (id(registry), metric_prefix)
    cached = _COLLECTORS.get(key)
    if cached is not None:
        return cached

    requests = Counter(
        f"{metric_prefix}_http_requests_total",
        "Total HTTP requests by operation.",
        labelnames=("operation", "method", "status"),
        registry=registry,
    )
    latency = Histogram(
        f"{metric_prefix}_http_request_duration_seconds",
        "HTTP request latency by operation.",
        labelnames=("operation", "method"),
        buckets=latency_buckets,
        registry=registry,
    )
    _COLLECTORS[key] = (requests, latency)
    return requests, latency


def _build_recorder(
    *,
    metric_prefix: str,
    operation_resolver: OperationResolver,
    registry: CollectorRegistry,
    latency_buckets: Sequence[float],
) -> Callable[[Info], None]:
    """Create request counter and latency histogram closures."""
    requests, latency = _get_or_create_collectors(
        metric_prefix=metric_prefix,
        registry=registry,
        latency_buckets=latency_buckets,
    )

    def record_service_metrics(info: Info) -> None:
        """Record request count and latency using low-cardinality labels."""
        operation = operation_resolver(info)
        requests.labels(operation, info.method, info.modified_status).inc()
        latency.labels(operation, info.method).observe(info.modified_duration)

    return record_service_metrics


def instrument_app(
    app: FastAPI,
    *,
    metric_prefix: str = "titiler",
    endpoint: str = "/metrics",
    operation_resolver: OperationResolver | None = None,
    excluded_handlers: Sequence[str] | None = None,
    should_ignore_untemplated: bool = True,
    include_in_schema: bool = False,
    registry: CollectorRegistry | None = None,
    latency_buckets: Sequence[float] = _DEFAULT_LATENCY_BUCKETS,
) -> Any:
    """Instrument a FastAPI app and expose a Prometheus scrape endpoint.

    This is an **app-level** helper (middleware + ``/metrics``). It is
    complementary to OpenTelemetry factory telemetry (``enable_telemetry``),
    which creates per-request traces for tile/render debugging.

    Collectors are shared per ``(registry, metric_prefix)`` so multiple apps
    can safely share the default Prometheus registry. The first call wins for
    ``latency_buckets``.

    Args:
        app: FastAPI application to instrument.
        metric_prefix: Prefix for metric names
            (e.g. ``titiler_http_requests_total``).
        endpoint: Path that exposes Prometheus metrics.
        operation_resolver: Callable mapping an Instrumentator ``Info`` object
            to a low-cardinality ``operation`` label. Defaults to
            :func:`default_operation_resolver`.
        excluded_handlers: Regex patterns for handlers that should not be
            instrumented. Defaults to ``/healthz`` and the scrape ``endpoint``
            (with optional trailing slash). When provided, the scrape endpoint
            is still always excluded.
        should_ignore_untemplated: Ignore requests without a matching route
            template (avoids high-cardinality raw paths by default).
        include_in_schema: Whether to include the scrape endpoint in OpenAPI.
        registry: Optional Prometheus registry. Defaults to the global registry.
        latency_buckets: Histogram buckets for request duration.

    Returns:
        The configured ``Instrumentator`` instance.

    Raises:
        ImportError: If the ``[metrics]`` extra is not installed.
    """
    if not metrics_available:
        raise _missing_metrics_extra()

    existing = getattr(app.state, _STATE_KEY, None)
    if existing is not None:
        return existing

    resolver = operation_resolver or default_operation_resolver
    metric_registry = registry if registry is not None else REGISTRY
    endpoint_pattern = _exclude_pattern(endpoint)

    if excluded_handlers is None:
        handlers = [_exclude_pattern("/healthz"), endpoint_pattern]
    else:
        handlers = list(excluded_handlers)
        if endpoint_pattern not in handlers:
            handlers.append(endpoint_pattern)

    recorder = _build_recorder(
        metric_prefix=metric_prefix,
        operation_resolver=resolver,
        registry=metric_registry,
        latency_buckets=latency_buckets,
    )

    instrumentator = (
        Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=should_ignore_untemplated,
            excluded_handlers=handlers,
            registry=metric_registry,
        )
        .add(recorder)
        .instrument(app)
        .expose(app, endpoint=endpoint, include_in_schema=include_in_schema)
    )

    setattr(app.state, _STATE_KEY, instrumentator)
    return instrumentator
