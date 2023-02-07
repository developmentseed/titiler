"""gdal WMTS service Extension."""

import xml.etree.ElementTree as ET
from typing import Literal
from urllib.parse import urlencode

from dataclasses import dataclass
from titiler.core.resources.responses import XMLResponse
from titiler.core.factory import BaseTilerFactory, FactoryExtension

from fastapi import Query, Depends
from starlette.requests import Request


@dataclass
class gdalwmtsExtension(FactoryExtension):
    """Add /wmts.xml endpoint to a TilerFactory."""

    def register(self, factory: BaseTilerFactory):  # noqa: C901
        """Register endpoint to the tiler factory."""

        @factory.router.get(
            "/wmts.xml",
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
        @factory.router.get(
            "/{TileMatrixSetId}/wmts.xml",
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
            TileMatrixSetId: Literal[tuple(factory.supported_tms.list())] = Query(  # type: ignore
                factory.default_tms,
                description=f"TileMatrixSet Name (default: '{factory.default_tms}')",
            ),
            url: str = Depends(factory.path_dependency),  # noqa
            bandscount: int = Query(..., description="Number of band returned by the tiler"),
            datatype: str = Query(..., description="Datatype returned by the tiler"),
            maxconnections: int = Query(None, description="Maximum number of simultaneous connections (defaults to 2)."),
            timeout: int = Query(None, description="Connection timeout in seconds (defaults to 30)."),
            cache: bool = Query(None, description="Allow local cache."),
        ):
            """Return a GDAL WMTS Service description."""
            route_params = {
                "TileMatrixSetId": TileMatrixSetId,
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
