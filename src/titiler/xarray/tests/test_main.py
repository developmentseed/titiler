"""Test titiler.xarray.main.app."""

import os
import subprocess
import sys


def test_telemetry_log_records_carry_service_name():
    """Log records carry the tracer provider's service name with telemetry on.

    Guards the order of the telemetry setup in `titiler.xarray.main`:
    instrumenting logging before setting the tracer provider leaves the
    service name empty on every log line.
    """
    # A subprocess, because the app reads the setting when imported, and the
    # tracer provider and logging instrumentation are process-wide.
    script = (
        "import logging\n"
        "import titiler.xarray.main\n"
        "print(logging.makeLogRecord({}).otelServiceName)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        env={**os.environ, "TITILER_XARRAY_API_TELEMETRY_ENABLED": "true"},
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout == "titiler\n"
