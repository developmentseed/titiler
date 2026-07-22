"""Prometheus HTTP metrics tests."""

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from fastapi import FastAPI
from prometheus_client import CollectorRegistry
from starlette.testclient import TestClient

from titiler.core import metrics
from titiler.core.metrics import (
    default_operation_resolver,
    get_route_path,
    instrument_app,
)


def _counter_total(registry: CollectorRegistry, metric_name: str) -> float:
    """Sum request counter samples for a metric name."""
    total = 0.0
    for collector in registry.collect():
        for sample in collector.samples:
            if sample.name == metric_name:
                total += sample.value
    return total


@pytest.fixture
def registry():
    """Isolated Prometheus registry for each test."""
    return CollectorRegistry()


def test_get_route_path_and_default_resolver():
    """Default resolver prefers operation_id, then name, then path."""
    app = FastAPI()

    @app.get("/hello", operation_id="say_hello", name="hello_route")
    def hello():
        return {"ok": True}

    instrument_app(
        app, metric_prefix="titiler_test_default", registry=CollectorRegistry()
    )

    with TestClient(app) as client:
        assert client.get("/hello").status_code == 200
        response = client.get("/metrics")
        assert response.status_code == 200
        assert 'operation="say_hello"' in response.text


def test_metrics_endpoint_returns_prometheus_output(registry):
    """Metrics returns Prometheus exposition with operation labels."""
    app = FastAPI()

    @app.get("/", operation_id="landing")
    def landing():
        return {"ok": True}

    instrument_app(app, metric_prefix="titiler_test", registry=registry)

    with TestClient(app) as client:
        assert client.get("/").status_code == 200
        response = client.get("/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        assert "titiler_test_http_requests_total{" in response.text
        assert 'operation="landing"' in response.text
        assert "titiler_test_http_request_duration_seconds_bucket{" in response.text
        assert 'status="2xx"' in response.text


def test_metrics_exclude_healthz_and_metrics(registry):
    """Health and scrape endpoints are not counted under any operation label."""
    app = FastAPI()

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    @app.get("/hello", operation_id="hello")
    def hello():
        return {"ok": True}

    instrument_app(app, metric_prefix="titiler_test_excl", registry=registry)

    with TestClient(app) as client:
        before = _counter_total(registry, "titiler_test_excl_http_requests_total")
        assert client.get("/healthz").status_code == 200
        assert client.get("/healthz/").status_code == 200
        assert client.get("/metrics").status_code == 200
        assert client.get("/metrics/").status_code == 200
        assert (
            _counter_total(registry, "titiler_test_excl_http_requests_total") == before
        )

        assert client.get("/hello").status_code == 200
        assert (
            _counter_total(registry, "titiler_test_excl_http_requests_total")
            == before + 1
        )


def test_custom_metrics_endpoint_excluded(registry):
    """A custom scrape endpoint is excluded from request counters."""
    app = FastAPI()

    @app.get("/hello", operation_id="hello")
    def hello():
        return {"ok": True}

    instrument_app(
        app,
        metric_prefix="titiler_test_prom",
        endpoint="/prom",
        registry=registry,
    )

    with TestClient(app) as client:
        before = _counter_total(registry, "titiler_test_prom_http_requests_total")
        assert client.get("/prom").status_code == 200
        assert client.get("/prom/").status_code == 200
        assert (
            _counter_total(registry, "titiler_test_prom_http_requests_total") == before
        )

        assert client.get("/hello").status_code == 200
        assert (
            _counter_total(registry, "titiler_test_prom_http_requests_total")
            == before + 1
        )
        body = client.get("/prom").text
        assert 'operation="hello"' in body


def test_status_codes_are_grouped(registry):
    """Status codes are grouped into classes like 2xx and 4xx."""
    app = FastAPI()

    @app.get("/ok", operation_id="ok")
    def ok():
        return {"ok": True}

    @app.get("/missing", operation_id="missing")
    def missing():
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="gone")

    instrument_app(app, metric_prefix="titiler_test_status", registry=registry)

    with TestClient(app) as client:
        assert client.get("/ok").status_code == 200
        assert client.get("/missing").status_code == 404
        body = client.get("/metrics").text
        assert 'status="2xx"' in body
        assert 'status="4xx"' in body


def test_untemplated_routes_ignored(registry):
    """Untemplated paths do not create raw path labels."""
    app = FastAPI()

    @app.get("/hello", operation_id="hello")
    def hello():
        return {"ok": True}

    instrument_app(app, metric_prefix="titiler_test_untemplated", registry=registry)

    with TestClient(app) as client:
        before = _counter_total(
            registry, "titiler_test_untemplated_http_requests_total"
        )
        assert client.get("/does-not-exist").status_code == 404
        assert (
            _counter_total(registry, "titiler_test_untemplated_http_requests_total")
            == before
        )
        body = client.get("/metrics").text
        assert "/does-not-exist" not in body


def test_custom_operation_resolver(registry):
    """Custom operation resolver maps templated route paths."""

    def resolve_operation(info):
        path = get_route_path(info)
        if path == "/searches/{search_id}/tiles/{z}/{x}/{y}":
            return "tiles"
        if path == "/hello":
            return "greeting"
        return "other"

    app = FastAPI()

    @app.get("/hello")
    def hello():
        return {"ok": True}

    @app.get("/searches/{search_id}/tiles/{z}/{x}/{y}")
    def tiles(search_id: str, z: int, x: int, y: int):
        return {"ok": True}

    instrument_app(
        app,
        metric_prefix="titiler_test_resolver",
        operation_resolver=resolve_operation,
        registry=registry,
    )

    with TestClient(app) as client:
        assert client.get("/hello").status_code == 200
        assert client.get("/searches/abc/tiles/1/2/3").status_code == 200
        body = client.get("/metrics").text
        assert 'operation="greeting"' in body
        assert 'operation="tiles"' in body
        assert "search_id" not in body
        assert 'operation="/hello"' not in body


def test_instrument_app_is_idempotent(registry):
    """Calling instrument_app twice on the same app is a no-op."""
    app = FastAPI()
    first = instrument_app(app, metric_prefix="titiler_test_idem", registry=registry)
    second = instrument_app(app, metric_prefix="titiler_test_idem", registry=registry)
    assert first is second

    metric_routes = [
        getattr(route, "path", None)
        for route in app.routes
        if getattr(route, "path", None) == "/metrics"
    ]
    assert len(metric_routes) == 1


def test_instrument_app_reuses_collectors_across_apps(registry):
    """Multiple apps can share a registry and metric prefix."""
    app_a = FastAPI()
    app_b = FastAPI()

    @app_a.get("/a", operation_id="route_a")
    def route_a():
        return {"ok": True}

    @app_b.get("/b", operation_id="route_b")
    def route_b():
        return {"ok": True}

    instrument_app(app_a, metric_prefix="titiler_test_shared", registry=registry)
    instrument_app(app_b, metric_prefix="titiler_test_shared", registry=registry)

    with TestClient(app_a) as client_a, TestClient(app_b) as client_b:
        assert client_a.get("/a").status_code == 200
        assert client_b.get("/b").status_code == 200
        body = client_a.get("/metrics").text
        assert 'operation="route_a"' in body
        assert 'operation="route_b"' in body
        assert (
            _counter_total(registry, "titiler_test_shared_http_requests_total") == 2.0
        )


def test_instrument_app_errors_without_metrics_extra(monkeypatch):
    """Calling instrument_app without metrics deps raises a clear ImportError."""
    monkeypatch.setattr(metrics, "metrics_available", False)
    app = FastAPI()
    with pytest.raises(ImportError, match=r"\[metrics\]"):
        instrument_app(app)


def test_default_operation_resolver_unknown():
    """Resolver returns unknown when no route metadata is available."""

    class _Req:
        scope = {}

    class _Info:
        request = _Req()
        modified_handler = "none"

    assert default_operation_resolver(_Info()) == "unknown"  # type: ignore[arg-type]


def test_multiprocess_metrics_exposition(tmp_path: Path):
    """Multiprocess scrape works when PROMETHEUS_MULTIPROC_DIR is set before import."""
    multiproc_dir = tmp_path / "multiproc"
    multiproc_dir.mkdir()
    script = textwrap.dedent(
        f"""
        import os

        os.environ["PROMETHEUS_MULTIPROC_DIR"] = {str(multiproc_dir)!r}

        from fastapi import FastAPI
        from starlette.testclient import TestClient

        from titiler.core.metrics import instrument_app

        app = FastAPI()

        @app.get("/", operation_id="landing")
        def landing():
            return {{"ok": True}}

        instrument_app(app, metric_prefix="titiler_test_mp")

        with TestClient(app) as client:
            assert client.get("/").status_code == 200
            response = client.get("/metrics")
            assert response.status_code == 200
            assert "titiler_test_mp_http_requests_total" in response.text
            assert 'operation="landing"' in response.text
        """
    )
    script_path = tmp_path / "check_multiproc.py"
    script_path.write_text(script)
    result = subprocess.run(
        [sys.executable, str(script_path)],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[3]),
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
    )
    assert result.returncode == 0, result.stderr


def test_optional_metrics_import_error(tmp_path: Path):
    """Missing prometheus packages leave metrics_available False after reload."""
    script = textwrap.dedent(
        """
        import builtins
        import importlib
        import sys

        real_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name.startswith("prometheus_"):
                raise ImportError(name)
            return real_import(name, globals, locals, fromlist, level)

        builtins.__import__ = fake_import
        sys.modules.pop("titiler.core.metrics", None)
        for key in list(sys.modules):
            if key.startswith("prometheus_"):
                sys.modules.pop(key, None)

        mod = importlib.import_module("titiler.core.metrics")
        assert mod.metrics_available is False
        """
    )
    script_path = tmp_path / "check_import_error.py"
    script_path.write_text(script)
    result = subprocess.run(
        [sys.executable, str(script_path)],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[3]),
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
    )
    assert result.returncode == 0, result.stderr
