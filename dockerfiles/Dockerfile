ARG PYTHON_VERSION=3.14

FROM python:${PYTHON_VERSION}  AS builder

# Set build labels
LABEL stage=builder
LABEL org.opencontainers.image.source="https://github.com/developmentseed/titiler"
LABEL org.opencontainers.image.description="TiTiler"
LABEL org.opencontainers.image.licenses="MIT"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libexpat1 curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Configure uv-managed virtual environment
ENV UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

WORKDIR /tmp

# Copy project metadata and code
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src/titiler/ ./src/titiler/
RUN uv sync --frozen --no-dev --no-editable --group server
RUN uv pip install --no-deps --no-editable .

# Runtime stage
FROM python:${PYTHON_VERSION}-slim

# Set runtime labels
LABEL org.opencontainers.image.source="https://github.com/developmentseed/titiler"
LABEL org.opencontainers.image.description="TiTiler"
LABEL org.opencontainers.image.licenses="MIT"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libexpat1 curl && \
    rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

RUN groupadd -g 1000 user && \
    useradd -u 1000 -g user -s /bin/bash -m user

USER user

###################################################
# For compatibility (might be removed at one point)
ENV MODULE_NAME=titiler.application.main
ENV VARIABLE_NAME=app
ENV HOST=0.0.0.0
ENV PORT=80
ENV WEB_CONCURRENCY=1
CMD gunicorn -k uvicorn.workers.UvicornWorker ${MODULE_NAME}:${VARIABLE_NAME} --bind ${HOST}:${PORT} --workers ${WEB_CONCURRENCY}
