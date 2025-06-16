
## Observability with OpenTelemetry

`TiTiler` provides built-in observability through OpenTelemetry, automatically creating traces for all API endpoints. These traces include detailed spans for key internal operations like data access and image processing, enabling fine-grained performance analysis and debugging.

This instrumentation works seamlessly with other OpenTelemetry libraries, such as FastAPIInstrumentor, to provide a complete, end-to-end view of your application's performance, from incoming request to final response.

### Installation

To enable telemetry, you must install titiler.core with the [telemetry] extra. This ensures all necessary OpenTelemetry packages are installed.

```bash
python -m pip install -U pip

# From Pypi
python -m pip install titiler.core[telemetry]

# Or from sources
git clone https://github.com/developmentseed/titiler.git
cd titiler && python -m pip install -e src/titiler/core[telemetry]
```

### Configuration

To export traces, you need to configure your application to send them to an observability platform (like Jaeger or Datadog) using an OTLP Exporter.

The following example demonstrates how to set up a tracer provider that exports data via the OTLP protocol over HTTP. This setup is typically done once when your application starts.

```python
# In your main application file, e.g., main.py

import os
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from titiler.core.factory import TilerFactory

# --- OpenTelemetry Configuration ---

# Define a "Resource" for your application.
# This adds metadata to your traces, like the service name and version.
resource = Resource.create(
    {
        SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "titiler"),
        SERVICE_VERSION: "0.1",
    }
)

# Create a "TracerProvider" with the defined resource.
# The provider manages the creation of tracers.
provider = TracerProvider(resource=resource)

# Configure an "Exporter" to send telemetry data.
# The OTLPSpanExporter sends data to an OTLP-compatible endpoint.
# By default, it reads the endpoint from the OTEL_EXPORTER_OTLP_ENDPOINT
# environment variable. The default for HTTP is http://localhost:4318.
exporter = OTLPSpanExporter()

# Use a "BatchSpanProcessor" to send spans in the background.
# This is the recommended processor for production.
processor = BatchSpanProcessor(exporter)
provider.add_span_processor(processor)

# Set the configured provider as the global tracer provider.
trace.set_tracer_provider(provider)

# --- FastAPI Application Setup ---
app = FastAPI(title="My TiTiler App")

# Instrument the FastAPI application.
# This adds middleware to trace requests, responses, and exceptions,
# complementing TiTiler's internal endpoint tracing.
FastAPIInstrumentor.instrument_app(app)

# Add your TiTiler endpoints
cog = TilerFactory()
app.include_router(cog.router)
```
