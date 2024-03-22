
**Goal**: add a `/wmts.xml` endpoint to return a GDAL WMTS service description XML file

**requirements**: titiler.extension >=0.11

1 - Create an extension

```python
# wmts.py
"""gdal WMTS service Extension."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlencode

from fastapi import Depends, Query
from starlette.requests import Request

from titiler.core.factory import BaseTilerFactory, FactoryExtension
from titiler.core.resources.responses import XMLResponse


@dataclass
class gdalwmtsExtension(FactoryExtension):
    """Add /wmts.xml endpoint to a TilerFactory."""

    def register(self, factory: BaseTilerFactory):  # noqa: C901
        """Register endpoint to the tiler factory."""

        @factory.router.get(
            "/{tileMatrixSetId}/wmts.xml",
            response_class=XMLResponse,
            responses={
                200: {
                    "description": "GDAL WMTS service description XML file",
                    "content": {
                        "application/xml": {},
                    },
                },
            },
        )
        def gdal_wmts(
            request: Request,
            tileMatrixSetId: Literal[tuple(factory.supported_tms.list())] = Path(  # type: ignore
                description="TileMatrixSet Name",
            ),
            url: str = Depends(factory.path_dependency),  # noqa
            bandscount: int = Query(
                ..., description="Number of band returned by the tiler"
            ),
            datatype: str = Query(..., description="Datatype returned by the tiler"),
            maxconnections: int = Query(
                None,
                description="Maximum number of simultaneous connections (defaults to 2).",
            ),
            timeout: int = Query(
                None, description="Connection timeout in seconds (defaults to 30)."
            ),
            cache: bool = Query(None, description="Allow local cache."),
        ):
            """Return a GDAL WMTS Service description."""
            route_params = {
                "tileMatrixSetId": tileMatrixSetId,
            }
            wmts_url = factory.url_for(request, "wmts", **route_params)

            qs_key_to_remove = [
                "tilematrixsetid",
                "bandscount",
                "datatype",
                "maxconnections",
                "timeout",
            ]
            qs = [
                (key, value)
                for (key, value) in request.query_params._list
                if key.lower() not in qs_key_to_remove
            ]
            if qs:
                wmts_url += f"?{urlencode(qs)}"

            maxconnections = maxconnections or 2
            timeout = timeout or 30

            xml = ET.Element("GDAL_WMTS")
            cap = ET.SubElement(xml, "GetCapabilitiesUrl")
            cap.text = wmts_url

            bandel = ET.SubElement(xml, "BandsCount")
            bandel.text = str(bandscount)
            datael = ET.SubElement(xml, "DataType")
            datael.text = datatype

            if cache:
                cacheel = ET.SubElement(xml, "Cache")

            connel = ET.SubElement(xml, "MaxConnections")
            connel.text = str(maxconnections)
            timeel = ET.SubElement(xml, "Timeout")
            timeel.text = str(timeout)
            codeel = ET.SubElement(xml, "ZeroBlockHttpCodes")
            codeel.text = "404"
            excepel = ET.SubElement(xml, "ZeroBlockOnServerException")
            excepel.text = "true"

            return XMLResponse(ET.tostring(xml))
```

2 - Create app and register our extension

```python
"""app.

app/main.py

"""

from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.factory import TilerFactory

from fastapi import FastAPI

from .wmts import gdalwmtsExtension

app = FastAPI(title="My simple app with custom TMS")

# Create  a set of endpoints using TilerFactory and add our extension
tiler = TilerFactory(extensions=[gdalwmtsExtension()])

app.include_router(tiler.router)
add_exception_handlers(app, DEFAULT_STATUS_CODES)
```


3 - Use it

```python
from rio_tiler.io import Reader

with Reader("http://0.0.0.0/WebMercatorQuad/wmts.xml?url=file.tif&bidx=1&bandscount=1&datatype=float32&tile_format=tif") as src:
    im = src.preview()
```

!!! Notes
    The `/wmts.xml` endpoint has no idea about the data itself and do not care about the `bidx` or `expression` which is why we need to
    set `bandscount` and `datatype` parameters.

    In the example above we use `tile_format=tif` so GDAL will fetch `tif` tiles and keep the datatype from the data (which we assume to be float32)
