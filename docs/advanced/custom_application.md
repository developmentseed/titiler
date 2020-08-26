# Create your own app

Titiler has been develloped so users can built their own app using only blocks they need. By default the titiler
app has `/cog`, `/stac` and `/tms` endpoints for COG and STAC support but some users will just want one.

```python
"""my_app.py"""

from titiler.endpoints import cog
from titiler.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from fastapi import Depends, FastAPI

from starlette.requests import Request
from starlette.responses import HTMLResponse

app = FastAPI(
    title="My super app",
    openapi_url="/api/openapi.json",
    description="It's something great",
)
app.include_router(cog.router, prefix="/cog", tags=["Cloud Optimized GeoTIFF"])
add_exception_handlers(app, DEFAULT_STATUS_CODES)

@app.get("/ping", description="Health Check", tags=["Health Check"])
def ping():
    """Health check."""
    return {"ping": "pong!"}
```

![](https://user-images.githubusercontent.com/10407788/88849256-a1ae5a80-d1b7-11ea-8383-cb01ac9287d4.png)

