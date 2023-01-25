"""wms Extension."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import numpy
import rasterio
from rasterio.crs import CRS
from rio_tiler.mosaic import mosaic_reader
from rio_tiler.mosaic.methods.base import MosaicMethodBase

from titiler.core.dependencies import RescalingParams
from titiler.core.factory import BaseTilerFactory, FactoryExtension
from titiler.core.resources.enums import ImageType, MediaType

from fastapi import Depends, HTTPException, Query

from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore

# TODO: mypy fails in python 3.9, we need to find a proper way to do this
templates = Jinja2Templates(directory=str(resources_files(__package__) / "templates"))  # type: ignore


class WMSMediaType(str, Enum):
    """Responses Media types for WMS"""

    tif = "image/tiff; application=geotiff"
    jp2 = "image/jp2"
    png = "image/png"
    jpeg = "image/jpeg"
    jpg = "image/jpg"
    webp = "image/webp"


class OverlayMethod(MosaicMethodBase):
    """Overlay data on top."""

    def feed(self, tile):
        """Add data to tile."""
        if self.tile is None:
            self.tile = tile

        pidex = self.tile.mask & ~tile.mask

        mask = numpy.where(pidex, tile.mask, self.tile.mask)
        self.tile = numpy.ma.where(pidex, tile, self.tile)
        self.tile.mask = mask


@dataclass
class wmsExtension(FactoryExtension):
    """Add /wms endpoint to a TilerFactory."""

    supported_crs: List[str] = field(default_factory=lambda: ["EPSG:4326"])
    supported_format: List[str] = field(
        default_factory=lambda: [
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/webp",
            "image/jp2",
            "image/tiff; application=geotiff",
        ]
    )
    supported_version: List[str] = field(
        default_factory=lambda: ["1.0.0", "1.1.1", "1.3.0"]
    )

    def register(self, factory: BaseTilerFactory):  # noqa: C901
        """Register endpoint to the tiler factory."""

        @factory.router.get(
            "/wms",
            response_class=Response,
            responses={
                200: {
                    "description": "Web Map Server responses",
                    "content": {
                        "application/xml": {},
                        "image/png": {},
                        "image/jpeg": {},
                        "image/jpg": {},
                        "image/webp": {},
                        "image/jp2": {},
                        "image/tiff; application=geotiff": {},
                    },
                },
            },
            openapi_extra={
                "parameters": [
                    {
                        "required": True,
                        "schema": {
                            "title": "Request name",
                            "type": "string",
                            "enum": [
                                "GetCapabilities",
                                "GetMap",
                            ],
                        },
                        "name": "REQUEST",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "WMS Service type",
                            "type": "string",
                            "enum": ["wms"],
                        },
                        "name": "SERVICE",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "WMS Request version",
                            "type": "string",
                            "enum": [
                                "1.1.0",
                                "1.1.1",
                                "1.3.0",
                            ],
                        },
                        "name": "VERSION",
                        "in": "query",
                    },
                    {
                        "required": True,
                        "schema": {
                            "title": "Comma-separated list of one or more map layers."
                        },
                        "name": "LAYERS",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Output format of service metadata/map",
                            "type": "string",
                            "enum": [
                                "application/xml",
                                "image/png",
                                "image/jpeg",
                                "image/jpg",
                                "image/webp",
                                "image/jp2",
                                "image/tiff; application=geotiff",
                            ],
                        },
                        "name": "FORMAT",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Sequence number or string for cache control"
                        },
                        "name": "UPDATESEQUENCE",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Coordinate reference system.",
                            "type": "string",
                        },
                        "name": "CRS",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Bounding box corners (lower left, upper right) in CRS units.",
                            "type": "string",
                        },
                        "name": "BBOX",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Width in pixels of map picture.",
                            "type": "integer",
                        },
                        "name": "WIDTH",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Height in pixels of map picture.",
                            "type": "integer",
                        },
                        "name": "HEIGHT",
                        "in": "query",
                    },
                    # Non-Used
                    {
                        "required": False,
                        "schema": {
                            "title": "Comma-separated list of one rendering style per requested layer."
                        },
                        "name": "STYLES",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Background transparency of map (default=FALSE).",
                            "type": "boolean",
                            "default": False,
                        },
                        "name": "TRANSPARENT",
                        "in": "query",
                    },
                    # {
                    #     "required": False,
                    #     "schema": {
                    #         "title": "Hexadecimal red-green-blue colour value for the background color (default=FFFFFF).",
                    #         "type": "string",
                    #         "default": "FFFFFF",
                    #     },
                    #     "name": "BGCOLOR",
                    #     "in": "query",
                    # },
                    {
                        "required": False,
                        "schema": {
                            "title": "The format in which exceptions are to be reported by the WMS (default=JSON).",
                            "type": "string",
                            "enum": ["JSON"],
                        },
                        "name": "EXCEPTIONS",
                        "in": "query",
                    },
                    # {
                    #     "required": False,
                    #     "schema": {
                    #         "title": "Time value of layer desired.",
                    #         "type": "string",
                    #     },
                    #     "name": "TIME",
                    #     "in": "query",
                    # },
                    # {
                    #     "required": False,
                    #     "schema": {
                    #         "title": "Elevation of layer desired.",
                    #         "type": "string",
                    #     },
                    #     "name": "ELEVATION",
                    #     "in": "query",
                    # },
                ]
            },
        )
        def wms(
            request: Request,
            # vendor (titiler) parameters
            layer_params=Depends(factory.layer_dependency),
            dataset_params=Depends(factory.dataset_dependency),
            post_process=Depends(factory.process_dependency),
            rescale: Optional[List[Tuple[float, ...]]] = Depends(RescalingParams),
            color_formula: Optional[str] = Query(
                None,
                title="Color Formula",
                description="rio-color formula (info: https://github.com/mapbox/rio-color)",
            ),
            colormap=Depends(factory.colormap_dependency),
            reader_params=Depends(factory.reader_dependency),
            env=Depends(factory.environment_dependency),
        ):
            """Return a WMS query for a single COG.

            GetCapability will generate a WMS XML definition.

            GetMap is mostly copied from titiler.core.factory.TilerFactory.part.part
            """
            req = {k.lower(): v for k, v in request.query_params.items()}

            # Request is mandatory
            request_type = req.get("request")
            if not request_type:
                raise HTTPException(
                    status_code=400, detail="Missing WMS 'REQUEST' parameter."
                )

            inlayers = req.get("layers")
            if inlayers is None:
                raise HTTPException(
                    status_code=400, detail="Missing WMS 'LAYERS' parameter."
                )

            layers = list(inlayers.split(","))
            if not layers or not inlayers:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid 'LAYERS' parameter: {inlayers}.",
                )

            # GetCapabilities: Return a WMS XML
            if request_type.lower() == "getcapabilities":
                # Required parameters:
                # - SERVICE=WMS
                # - REQUEST=GetCapabilities
                # Optional parameters: VERSION, FORMAT, UPDATESEQUENCE

                # List of required parameters (layers is added for titiler)
                req_keys = {"service", "request", "layers"}

                intrs = set(req.keys()).intersection(req_keys)
                missing_keys = req_keys.difference(intrs)
                if len(missing_keys) > 0:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing 'GetCapabilities' parameters: {missing_keys}",
                    )

                if not req["service"].lower() == "wms":
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid 'SERVICE' parameter: {req['service']}. Only 'wms' is accepted",
                    )

                version = req.get("version", "1.3.0")
                if version not in self.supported_version:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid 'VERSION' parameter: {version}. Allowed versions include: {self.supported_version}",
                    )

                wms_url = factory.url_for(request, "wms")

                qs_key_to_remove = [
                    "service",
                    "request",
                    "layers",
                    "version",
                    "format",
                    "updatesequence",
                ]
                qs = [
                    (key, value)
                    for (key, value) in request.query_params._list
                    if key.lower() not in qs_key_to_remove
                ]
                if qs:
                    wms_url += f"?{urlencode(qs)}"

                # Grab information from each layer provided
                layers_dict: Dict[str, Any] = {}
                for layer in layers:
                    layers_dict[layer] = {}
                    with rasterio.Env(**env):
                        with factory.reader(layer, **reader_params) as src_dst:
                            layers_dict[layer]["srs"] = f"EPSG:{src_dst.crs.to_epsg()}"
                            layers_dict[layer]["bounds"] = src_dst.bounds
                            layers_dict[layer][
                                "bounds_wgs84"
                            ] = src_dst.geographic_bounds
                            layers_dict[layer]["abstract"] = src_dst.info().json()

                # Build information for the whole service
                minx, miny, maxx, maxy = zip(
                    *[layers_dict[layer]["bounds_wgs84"] for layer in layers_dict]
                )

                return templates.TemplateResponse(
                    f"wms_{version}.xml",
                    {
                        "request": request,
                        "request_url": wms_url,
                        "formats": self.supported_format,
                        "available_epsgs": self.supported_crs,
                        "layers_dict": layers_dict,
                        "service_dict": {
                            "xmin": min(minx),
                            "ymin": min(miny),
                            "xmax": max(maxx),
                            "ymax": max(maxy),
                        },
                    },
                    media_type=MediaType.xml.value,
                )

            # GetMap: Return an image chip
            if request_type.lower() == "getmap":
                # Required parameters:
                # - VERSION
                # - REQUEST=GetMap,
                # - LAYERS
                # - STYLES
                # - CRS
                # - BBOX
                # - WIDTH
                # - HEIGHT
                # - FORMAT
                # Optional parameters: TRANSPARENT, BGCOLOR, EXCEPTIONS, TIME, ELEVATION, ...

                # List of required parameters (styles and crs are excluded)
                req_keys = {
                    "version",
                    "request",
                    "layers",
                    "bbox",
                    "width",
                    "height",
                    "format",
                }

                intrs = set(req.keys()).intersection(req_keys)
                missing_keys = req_keys.difference(intrs)
                if len(missing_keys) > 0:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing 'GetMap' parameters: {missing_keys}",
                    )

                version = req["version"]
                if version not in self.supported_version:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid 'VERSION' parameter: {version}. Allowed versions include: {self.supported_version}",
                    )

                if not set(req.keys()).intersection({"crs", "srs"}):
                    raise HTTPException(
                        status_code=400, detail="Missing 'CRS' or 'SRS parameters."
                    )

                crs_value = req.get("crs", req.get("srs"))
                if not crs_value:
                    raise HTTPException(
                        status_code=400, detail="Invalid 'CRS' parameter."
                    )

                crs = CRS.from_user_input(crs_value)

                bbox = list(map(float, req["bbox"].split(",")))
                if len(bbox) != 4:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid 'BBOX' parameters: {req['bbox']}. Needs 4 coordinates separated by commas",
                    )

                if version == "1.3.0":
                    # WMS 1.3.0 is lame and flips the coords of EPSG:4326
                    # EPSG:4326 refers to WGS 84 geographic latitude, then longitude.
                    # That is, in this CRS the x axis corresponds to latitude, and the y axis to longitude.
                    if crs == CRS.from_epsg(4326):
                        bbox = [
                            bbox[1],
                            bbox[0],
                            bbox[3],
                            bbox[2],
                        ]

                    # Overwrite CRS:84 with EPSG:4326 when specified
                    # “CRS:84” refers to WGS 84 geographic longitude and latitude expressed in decimal degrees
                    elif crs == CRS.from_user_input("CRS:84"):
                        crs = CRS.from_epsg(4326)

                if transparent := req.get("transparent", False):
                    if str(transparent).lower() == "true":
                        transparent = True

                    elif str(transparent).lower() == "false":
                        transparent = False

                    else:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid 'TRANSPARENT' parameter: {transparent}. Should be one of ['FALSE', 'TRUE'].",
                        )

                if req["format"] not in self.supported_format:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid 'FORMAT' parameter: {req['format']}. Should be one of {self.supported_format}.",
                    )
                format = ImageType(WMSMediaType(req["format"]).name)

                height, width = int(req["height"]), int(req["width"])

                def _reader(src_path: str):
                    with rasterio.Env(**env):
                        with factory.reader(src_path, **reader_params) as src_dst:
                            return src_dst.part(
                                bbox,
                                width=width,
                                height=height,
                                dst_crs=crs,
                                bounds_crs=crs,
                                **layer_params,
                                **dataset_params,
                            )

                image, assets_used = mosaic_reader(
                    layers,
                    _reader,
                    pixel_selection=OverlayMethod(),
                )

                if post_process:
                    image = post_process(image)

                if rescale:
                    image.rescale(rescale)

                if color_formula:
                    image.apply_color_formula(color_formula)

                content = image.render(
                    img_format=format.driver,
                    colormap=colormap,
                    add_mask=transparent,
                    **format.profile,
                )

                return Response(content, media_type=format.mediatype)

            elif request_type.lower() == "getfeatureinfo":
                return Response("Not Implemented", 400)

            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid 'REQUEST' parameter: {request_type}. Should be one of ['GetCapabilities', 'GetMap'].",
                )
