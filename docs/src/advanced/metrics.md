
## Observability with Prometheus Metrics

`TiTiler` provides optional **app-level** Prometheus HTTP metrics that complement OpenTelemetry factory telemetry.

| Signal | Purpose | Attachment | Export |
| --- | --- | --- | --- |
| OpenTelemetry traces | Per-request debugging of tile/render paths | Factory (`enable_telemetry`) | OTLP push |
| Prometheus metrics | Request count / latency for dashboards and alerting | Application (`instrument_app`) | `/metrics` scrape |

Metrics are **not** attached to `BaseFactory`. Instrumentation is middleware plus a scrape endpoint. By default, labels use low-cardinality `operation` values (route metadata) and untemplated paths are ignored.

See also: [Observability with OpenTelemetry](telemetry.md).

### Installation

```bash
python -m pip install -U pip

# From PyPI
python -m pip install 'titiler.core[metrics]'

# Or from sources
git clone https://github.com/developmentseed/titiler.git
cd titiler && python -m pip install -e 'src/titiler/core[metrics]'
```

### Configuration

```python
from fastapi import FastAPI

from titiler.core.factory import TilerFactory
from titiler.core.metrics import instrument_app

app = FastAPI(title="My TiTiler App")
cog = TilerFactory()
app.include_router(cog.router, prefix="/cog")

# App-level Prometheus metrics (optional; enable in your own settings/flag)
instrument_app(app, endpoint="/metrics")
```

Once instrumented, `/metrics` exposes:

- `{metric_prefix}_http_requests_total{operation,method,status}`
- `{metric_prefix}_http_request_duration_seconds{operation,method}`

Defaults:

- `metric_prefix="titiler"`
- Status codes grouped (`2xx`, `4xx`, `5xx`)
- `/healthz` and the scrape endpoint excluded (including trailing-slash variants)
- Untemplated routes (for example bare 404s) ignored

Collectors are shared per `(registry, metric_prefix)`, so multiple apps can use the same Prometheus registry safely.

### Custom operation labels

Supply a resolver that maps templated route paths to stable operation names:

```python
from titiler.core.metrics import get_route_path, instrument_app


def resolve_operation(info):
    path = get_route_path(info)
    if path and "/tiles/" in path:
        return "tiles"
    if path == "/":
        return "landing"
    return "other"


instrument_app(
    app,
    metric_prefix="titiler_app",
    operation_resolver=resolve_operation,
)
```

Decide when to enable metrics in your application's own settings, and call `instrument_app` only when it is turned on.

### Multi-worker deployments

For multi-worker deployments (for example `uvicorn --workers N` or Gunicorn), set
`PROMETHEUS_MULTIPROC_DIR` to an existing writable directory **before** the
application is imported, and clear that directory before each server start.

```bash
export PROMETHEUS_MULTIPROC_DIR=/tmp/titiler-prometheus
mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
rm -rf "$PROMETHEUS_MULTIPROC_DIR"/*
```

With Gunicorn, also mark workers dead on exit so stale metric files are cleaned up:

```python
from prometheus_client import multiprocess


def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)
```
