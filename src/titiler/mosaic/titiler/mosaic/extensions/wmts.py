"""titiler.mosaic wmts extensions."""

import warnings
from collections.abc import Callable
from typing import Annotated, Any
from urllib.parse import urlencode

import jinja2
import rasterio
from attrs import define, field
from fastapi import Depends, HTTPException, Query
from morecantile.models import crs_axis_inverted
from rasterio.crs import CRS
from rio_tiler.constants import WGS84_CRS
from rio_tiler.mosaic.backend import BaseBackend
from rio_tiler.utils import CRS_to_urn
from starlette.datastructures import QueryParams
from starlette.requests import Request
from starlette.templating import Jinja2Templates

from titiler.core.factory import FactoryExtension
from titiler.core.resources.enums import ImageType
from titiler.core.resources.responses import XMLResponse
from titiler.core.utils import check_query_params, rio_crs_to_pyproj, tms_limits
from titiler.mosaic.factory import MosaicTilerFactory

jinja2_env = jinja2.Environment(
    autoescape=jinja2.select_autoescape(["xml"]),
    loader=jinja2.ChoiceLoader([jinja2.PackageLoader(__package__, "templates")]),
)
DEFAULT_TEMPLATES = Jinja2Templates(env=jinja2_env)


@define
class wmtsExtension(FactoryExtension):
    """RESTful WMTS service Extension for MosaicTilerFactory."""

    # Geographic Coordinate Reference System.
    crs: CRS = field(default=WGS84_CRS)

    templates: Jinja2Templates = field(default=DEFAULT_TEMPLATES)

    get_renders: Callable[[BaseBackend], dict[str, dict[str, Any]]] = field(
        default=lambda obj: {}
    )

    def register(self, factory: MosaicTilerFactory):  # type: ignore [override] # noqa: C901
        """Register endpoint to the tiler factory."""

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
        )
        def wmts(  # noqa: C901
            request: Request,
            tile_format: Annotated[
                ImageType,
                Query(description="Output image type. Default is png."),
            ] = ImageType.png,
            tile_scale: Annotated[
                int,
                Query(
                    gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
                ),
            ] = 1,
            use_epsg: Annotated[
                bool,
                Query(
                    description="Use EPSG code, not opengis.net, for the ows:SupportedCRS in the TileMatrixSet (set to True to enable ArcMap compatability)"
                ),
            ] = False,
            src_path=Depends(factory.path_dependency),
            backend_params=Depends(factory.backend_dependency),
            reader_params=Depends(factory.reader_dependency),
            env=Depends(factory.environment_dependency),
        ):
            """OGC RESTful WMTS endpoint."""
            with rasterio.Env(**env):
                with factory.backend(
                    src_path,
                    reader=factory.dataset_reader,
                    reader_options=reader_params.as_dict(),
                    **backend_params.as_dict(),
                ) as src_dst:
                    bounds = src_dst.get_geographic_bounds(self.crs)
                    default_renders = self.get_renders(src_dst)

                # List of dependencies a `/tile` URL should validate
                # Note: Those dependencies should only require Query() inputs
                tile_dependencies: list[Callable] = [
                    factory.layer_dependency,
                    factory.dataset_dependency,
                    factory.pixel_selection_dependency,
                    factory.process_dependency,
                    factory.colormap_dependency,
                    factory.render_dependency,
                    factory.tile_dependency,
                    factory.assets_accessor_dependency,
                    factory.reader_dependency,
                    factory.backend_dependency,
                ]
                renders: list[dict[str, Any]] = []

                ##########################################
                # 1. Create layers from `renders` metadata
                for name, values in default_renders.items():
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
                    "tile_scale",
                    "use_epsg",
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
                    renders.append({"name": "default", "query_string": qs})

                #################################################
                # 3. if there is no layers we raise and exception
                if not renders:
                    raise HTTPException(
                        status_code=400,
                        detail="Could not find any valid layers in metadata or construct one from Query Parameters.",
                    )

                layers: list[dict[str, Any]] = []
                title = src_path if isinstance(src_path, str) else "TiTiler Mosaic"

                for render in renders:
                    for tms_id in factory.supported_tms.list():
                        tms = factory.supported_tms.get(tms_id)
                        try:
                            with factory.backend(
                                src_path,
                                tms=tms,
                                reader=factory.dataset_reader,
                                reader_options=reader_params.as_dict(),
                                **backend_params.as_dict(),
                            ) as src_dst:
                                # NOTE: Custom TiTiler Render key in form of {"tilematrixsets": {"{TMS_ID}": (minzoom, maxzoom)}}
                                if zooms := render.get("tilematrixsets", {}).get(
                                    tms_id
                                ):
                                    minzoom, maxzoom = zooms
                                else:
                                    minzoom = src_dst.minzoom
                                    maxzoom = src_dst.maxzoom

                                # NOTE: Custom TiTiler Render key in form of {"spatial_extent": (minx, miny, maxx, maxy)}
                                # NOTE: We assume the spatial_extent is always in WGS84
                                if render.get("spatial_extent"):
                                    bbox = render["spatial_extent"]
                                    crs = WGS84_CRS
                                else:
                                    bbox = bounds
                                    crs = self.crs

                                tilematrixset_limits = tms_limits(
                                    tms,
                                    bbox,
                                    zooms=(minzoom, maxzoom),
                                    geographic_crs=crs,
                                )

                        except Exception as e:  # noqa
                            pass

                        route_params = {
                            "z": "{TileMatrix}",
                            "x": "{TileCol}",
                            "y": "{TileRow}",
                            "scale": tile_scale,
                            "format": tile_format.value,
                            "tileMatrixSetId": tms_id,
                        }

                        bbox_crs_type = "WGS84BoundingBox"
                        bbox_crs_uri = "urn:ogc:def:crs:OGC:2:84"
                        if crs != WGS84_CRS:
                            bbox_crs_type = "BoundingBox"
                            bbox_crs_uri = CRS_to_urn(crs)  # type: ignore
                            # WGS88BoundingBox is always xy ordered, but BoundingBox must match the CRS order
                            proj_crs = rio_crs_to_pyproj(crs)
                            if crs_axis_inverted(proj_crs):
                                # match the bounding box coordinate order to the CRS
                                bbox = [bbox[1], bbox[0], bbox[3], bbox[2]]

                        layers.append(
                            {
                                "title": f"{title}_{tms_id}_{render['name']}",
                                "identifier": f"{title}_{tms_id}_{render['name']}",
                                "tms_identifier": tms_id,
                                "tms_limits": tilematrixset_limits,
                                "tiles_url": factory.url_for(
                                    request, "tile", **route_params
                                ),
                                "query_string": render["query_string"],
                                "bbox_crs_type": bbox_crs_type,
                                "bbox_crs_uri": bbox_crs_uri,
                                "bbox": bbox,
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
                    {
                        "id": tms_id,
                        "crs": supported_crs,
                        "matrices": tms.tileMatrices,
                    }
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
