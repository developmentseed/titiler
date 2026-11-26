"""Test titiler.application.main.app."""

import os
import subprocess
import sys


def test_health(app):
    """Test /healthz endpoint."""
    response = app.get("/healthz")
    assert response.status_code == 200
    resp = response.json()
    assert set(resp["versions"].keys()) == {
        "titiler",
        "gdal",
        "geos",
        "proj",
        "rasterio",
        "zarr",
        "xarray",
    }

    response = app.get("/api")
    assert response.status_code == 200

    response = app.get("/api.html")
    assert response.status_code == 200


def test_telemetry_log_records_carry_service_name():
    """Log records carry the tracer provider's service name with telemetry on.

    Guards the order of the telemetry setup in `titiler.application.main`:
    instrumenting logging before setting the tracer provider leaves the
    service name empty on every log line.
    """
    # A subprocess, because the app reads the setting when imported, and the
    # tracer provider and logging instrumentation are process-wide.
    script = (
        "import logging\n"
        "import titiler.application.main\n"
        "print(logging.makeLogRecord({}).otelServiceName)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        env={**os.environ, "TITILER_API_TELEMETRY_ENABLED": "true"},
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout == "titiler\n"
