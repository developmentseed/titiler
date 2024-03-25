
**ref**: https://github.com/developmentseed/titiler/discussions/331

**Goal**: allow users to pass signed url or url containing query parameters (delimited with `&`)

**requirements**: titiler.core

## What / Why / How

Passing a signed URL or a complex URL for a dataset is not supported by default in TiTiler because the parameters (delimited with `&`) from the signed url conflict with the query parameters from the application itself. In order to allow signed url in the application there are two solutions:


### 1. URL Encoding

#### 1.1 Full URL

The easiest way (from the application's point of view) to allow complex URLs is to allow an encoded url as an input parameter.

```python
import base64
url = "http://my.dataset.com/cog.tif?p=aaa&c&1234&t=4321"

# base64.b64encode(url.encode())
>>> "aHR0cDovL215LmRhdGFzZXQuY29tL2NvZy50aWY/cD1hYWEmYyYxMjM0JnQ9NDMyMQ=="
```

When base64 encoded, the url is just a regular string and thus will be valid in the application.

```python
"""Minimal COG tiler with Signed URL support."""

import base64
from titiler.core.factory import TilerFactory
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from fastapi import FastAPI


# Custom Path dependency which can `decode` a base64 url
def DatasetPathParams(
    url: str = Query(..., description="Dataset URL"),
    base64_encoded: bool = Query(None)
) -> str:
    """Create dataset path from args"""
    if base64_encoded:
        url = base64.b64decode(url).decode()
    return url

app = FastAPI(title="My simple app")

cog = TilerFactory(path_dependency=DatasetPathParams)
app.include_router(cog.router, tags=["Cloud Optimized GeoTIFF"])

add_exception_handlers(app, DEFAULT_STATUS_CODES)


@app.get("/healthz", description="Health Check", tags=["Health Check"])
def ping():
    """Health check."""
    return {"ping": "pong!"}
```

```python
import base64
from my_provider import signed_url

my_url = "https://dataset.com/...."

# Get signed URL
my_signed_url = signed_url(my_url)

# Encode the signed url using base64
url = base64.b64encode(my_signed_url.encode())

info = request.get(f"{titiler_endpoint}/info", params={"url": url, signed_url: True})
```

#### 1.2 Encode only the url params

```python
"""Minimal COG tiler with Signed URL support."""

import base64
from titiler.core.factory import TilerFactory
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from fastapi import FastAPI


# Another solution is to pass only the query parameters encoded in base64
def DatasetPathParams(
    url: str = Query(..., description="Dataset URL"),
    url_params: str = Query(
        None, description="Base64 encoded Query parameters to add to the dataset URL."
    ),
) -> str:
    """DatasetPath Params."""
    if url_params:
        url += f"?{b64decode(url_params).decode()}"
    return url


app = FastAPI(title="My simple app")

cog = TilerFactory(path_dependency=DatasetPathParams)
app.include_router(cog.router, tags=["Cloud Optimized GeoTIFF"])

add_exception_handlers(app, DEFAULT_STATUS_CODES)


@app.get("/healthz", description="Health Check", tags=["Health Check"])
def ping():
    """Health check."""
    return {"ping": "pong!"}
```

```python
import base64
from urllib.parse import urlparse
from my_provider import signed_url

my_url = "https://dataset.com/...."

# Get signed URL
my_signed_url = signed_url(my_url)

# Extract the url parameters
signed_params = urlparse(my_signed_url).query

# Encode the parameters using base64
encoded_params = base64.b64encode(signed_params.encode())

info = request.get(f"{titiler_endpoint}/info", params={"url": url, url_params: encoded_params})
```

### 2. Signing URL in the application

Another solution is to sign the URL directly in TiTiler.

```python
"""Minimal COG tiler with Signed URL support."""

import my_provider  # e.g AWS, Google, ...

from titiler.core.factory import TilerFactory
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from fastapi import FastAPI


# Custom Path dependency which will sign url
# !!! You may want to add caching here to avoid to many call to the signing provider !!!
def DatasetPathParams(
    url: str = Query(..., description="Dataset URL"),
) -> str:
    """Create dataset path from args"""
    # Use your provider library to sign the URL
    return my_provider.sign(url)


app = FastAPI(title="My simple app")

cog = TilerFactory(path_dependency=DatasetPathParams)
app.include_router(cog.router, tags=["Cloud Optimized GeoTIFF"])

add_exception_handlers(app, DEFAULT_STATUS_CODES)


@app.get("/healthz", description="Health Check", tags=["Health Check"])
def ping():
    """Health check."""
    return {"ping": "pong!"}
```

```python
import base64
from my_provider import signed_url

my_url = "https://dataset.com/...."

info = request.get(f"{titiler_endpoint}/info", params={"url": my_url})
```
