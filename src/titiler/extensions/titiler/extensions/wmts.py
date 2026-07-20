"""TiTiler WMTS Extension."""

import warnings
from collections.abc import Callable
from typing import Annotated, Any, cast
from urllib.parse import urlencode

import jinja2
import rasterio
from attrs import define, field
from fastapi import Depends, HTTPException, Query
from morecantile.models import crs_axis_inverted
from rasterio.crs import CRS
from rio_tiler.constants import WGS84_CRS
from rio_tiler.io import BaseReader
from rio_tiler.utils import CRS_to_urn
from starlette.datastructures import QueryParams
from starlette.requests import Request
from starlette.templating import Jinja2Templates

from titiler.core.dependencies import ZoomsParams
from titiler.core.factory import FactoryExtension, TilerFactory
from titiler.core.resources.enums import ImageType
from titiler.core.resources.responses import XMLResponse
from titiler.core.utils import (
    check_query_params,
    dependencies_to_openapi_params,
    rio_crs_to_pyproj,
    tms_limits,
)

jinja2_env = jinja2.Environment(
    autoescape=jinja2.select_autoescape(["xml"]),
    loader=jinja2.ChoiceLoader([jinja2.PackageLoader(__package__, "templates")]),
)
DEFAULT_TEMPLATES = Jinja2Templates(env=jinja2_env)


@define
class wmtsExtension(FactoryExtension):
    """RESTful WMTS service Extension for TilerFactory."""

    # Geographic Coordinate Reference System.
    crs: CRS = field(default=WGS84_CRS)

    templates: Jinja2Templates = field(default=DEFAULT_TEMPLATES)

    # TODO: Remove in 3.0
    get_renders: Callable[[BaseReader], dict[str, dict[str, Any]]] | None = field(
        default=None
    )

    # List of dependencies a `/tile` URL should validate
    # Note: Those dependencies should only require Query() inputs
    tile_dependencies: list[Callable] | None = field(default=None)

    # TODO: Remove in 3.0
    def __attrs_post_init__(self):
        """Warn about deprecation of `get_renders` attribute."""
        if self.get_renders:
            warnings.warn(
                "The wmtsExtension's `get_renders` attribute is deprecated and will be ignored. Please set it at the factory level.",
                DeprecationWarning,
                stacklevel=2,
            )

    def register(self, factory: TilerFactory):  # type: ignore [override] # noqa: C901
        """Register extension's endpoints."""

        tile_dependencies = (
            self.tile_dependencies
            if self.tile_dependencies is not None
            else [
                factory.reader_dependency,
                factory.tile_dependency,
                factory.layer_dependency,
                factory.dataset_dependency,
                factory.process_dependency,
                factory.colormap_dependency,
                factory.render_dependency,
            ]
        )
        tile_dependencies = cast(list[Callable], tile_dependencies)

        @factory.router.get(
            "/WMTSCapabilities.xml",
            response_class=XMLResponse,
            responses={
                200: {
                    "content": {"application/xml": {}},
                    "description": "Return RESTful WMTS service capabilities document.",
                }
            },
            operation_id=f"{factory.operation_prefix}getWMTS",
            openapi_extra={
                "parameters": dependencies_to_openapi_params(tile_dependencies),
            },
        )
        def wmts(  # noqa: C901
            request: Request,
            tile_format: Annotated[
                ImageType,
                Query(description="Output image type. Default is png."),
            ] = ImageType.png,
            use_epsg: Annotated[
                bool,
                Query(
                    description="Use EPSG code, not opengis.net, for the ows:SupportedCRS in the TileMatrixSet (set to True to enable ArcMap compatability)"
                ),
            ] = False,
            src_path=Depends(factory.path_dependency),
            zooms=Depends(ZoomsParams),
            reader_params=Depends(factory.reader_dependency),
            env=Depends(factory.environment_dependency),
        ):
            """OGC RESTful WMTS endpoint."""
            with rasterio.Env(**env):
                with factory.reader(src_path, **reader_params.as_dict()) as src_dst:
                    dataset_bounds = src_dst.get_geographic_bounds(self.crs)

                    # TODO: Remove in 3.0
                    # and use factory.get_renders instead
                    get_renders: Callable[[BaseReader], dict[str, dict[str, Any]]] = (
                        self.get_renders or factory.get_renders
                    )
                    default_renders = get_renders(src_dst)

                renders: list[dict[str, Any]] = []

                ##########################################
                # 1. Create layers from `renders` metadata
                for name, values in default_renders.items():
                    values.pop("tilesize", None)  # Ensure tilesize is not overridden
                    if check_query_params(tile_dependencies, values):
                        renders.append(
                            {
                                "name": name,
                                "query_string": urlencode(values, doseq=True)
                                if values
                                else None,
                                "tilematrixsets": values.get("tilematrixsets", {}),
                                "spatial_extent": values.get("spatial_extent", None),
                            }
                        )
                    else:
                        warnings.warn(
                            f"Cannot construct URL for layer `{name}`",
                            UserWarning,
                            stacklevel=2,
                        )

                #######################################
                # 2. Create layer from query-parameters
                qs_key_to_remove = [
                    "tile_format",
                    "use_epsg",
                    # Make sure tilesize is not ovewrriden from WMTS request
                    "tilesize",
                    # tilematrixset metadata
                    "zooms",
                    # OGC WMTS parameters to ignore
                    "service",
                    "request",
                    "acceptversions",
                    "sections",
                    "updatesequence",
                    "acceptformats",
                ]

                qs = urlencode(
                    [
                        (key, value)
                        for (key, value) in request.query_params._list
                        if key.lower() not in qs_key_to_remove
                    ],
                    doseq=True,
                )

                if check_query_params(tile_dependencies, QueryParams(qs)):
                    renders.append(
                        {"name": "default", "query_string": qs, "tilematrixsets": zooms}
                    )

                #################################################
                # 3. if there is no layers we raise and exception
                if not renders:
                    raise HTTPException(
                        status_code=400,
                        detail="Could not find any valid layers in metadata or construct one from Query Parameters.",
                    )

                layers: list[dict[str, Any]] = []
                title = src_path if isinstance(src_path, str) else "TiTiler"
                for render in renders:
                    # NOTE: Default bounds and CRS for the dataset
                    bounds = dataset_bounds
                    geographic_crs = self.crs

                    # NOTE: Custom TiTiler Render key in form of {"spatial_extent": (minx, miny, maxx, maxy)}
                    # NOTE: We assume the spatial_extent is always in WGS84
                    if render.get("spatial_extent"):
                        bounds = render["spatial_extent"]
                        geographic_crs = WGS84_CRS

                    bbox_crs_type = "WGS84BoundingBox"
                    bbox_crs_uri = "urn:ogc:def:crs:OGC:2:84"
                    wmts_bbox = bounds
                    if geographic_crs != WGS84_CRS:
                        bbox_crs_type = "BoundingBox"
                        crs_urn = CRS_to_urn(geographic_crs)
                        if not crs_urn:
                            warnings.warn(
                                f"Could not resolve a URN for CRS '{geographic_crs}', falling back to WKT for the BoundingBox crs attribute",
                                UserWarning,
                                stacklevel=2,
                            )
                            crs_urn = geographic_crs.to_wkt()
                        bbox_crs_uri = crs_urn
                        # WGS88BoundingBox is always xy ordered, but BoundingBox must match the CRS order
                        proj_crs = rio_crs_to_pyproj(geographic_crs)
                        if crs_axis_inverted(proj_crs):
                            # match the bounding box coordinate order to the CRS
                            wmts_bbox = [
                                wmts_bbox[1],
                                wmts_bbox[0],
                                wmts_bbox[3],
                                wmts_bbox[2],
                            ]

                    # NOTE: Custom TiTiler Render key in form of {"tilematrixsets": {"{tms_id}": (minzoom, maxzoom)}}
                    tilematrixsets = render.get("tilematrixsets", {})

                    for tms_id in factory.supported_tms.list():
                        tms = factory.supported_tms.get(tms_id)

                        # NOTE: If zooms are not in render then we get them from the dataset
                        tms_zooms: tuple[int, int] | None = tilematrixsets.get(
                            tms_id
                        ) or tilematrixsets.get("*")
                        if not tms_zooms:
                            try:
                                with factory.reader(
                                    src_path, tms=tms, **reader_params.as_dict()
                                ) as src_dst:
                                    tms_zooms = (src_dst.minzoom, src_dst.maxzoom)
                            except Exception as e:  # noqa
                                tms_zooms = (tms.minzoom, tms.maxzoom)

                        tilematrixset_limits = tms_limits(
                            tms,
                            bounds,
                            zooms=tms_zooms,
                            geographic_crs=geographic_crs,
                        )

                        route_params = {
                            "z": "{TileMatrix}",
                            "x": "{TileCol}",
                            "y": "{TileRow}",
                            "format": tile_format.value,
                            "tileMatrixSetId": tms_id,
                        }
                        tile_url = factory.url_for(request, "tile", **route_params)

                        layers.append(
                            {
                                "title": f"{title}_{tms_id}_{render['name']}",
                                "identifier": f"{title}_{tms_id}_{render['name']}",
                                "tms_identifier": tms_id,
                                "tms_limits": tilematrixset_limits,
                                "tiles_url": tile_url,
                                "query_string": render["query_string"],
                                "bbox_crs_type": bbox_crs_type,
                                "bbox_crs_uri": bbox_crs_uri,
                                "bbox": wmts_bbox,
                            }
                        )

            tileMatrixSets: list[dict[str, Any]] = []
            for tms_id in factory.supported_tms.list():
                tms = factory.supported_tms.get(tms_id)
                if use_epsg:
                    supported_crs = f"EPSG:{tms.crs.to_epsg()}"
                else:
                    supported_crs = tms.crs.srs

                tileMatrixSets.append(
                    {"id": tms_id, "crs": supported_crs, "matrices": tms.tileMatrices}
                )

            return self.templates.TemplateResponse(
                request,
                name="wmts.xml",
                context={
                    "layers": layers,
                    "tileMatrixSets": tileMatrixSets,
                    "media_type": tile_format.mediatype,
                },
                media_type="application/xml",
            )
