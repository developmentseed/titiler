"""TiTiler WMTS Extension."""

from typing import Annotated, Any
from urllib.parse import urlencode

import jinja2
import rasterio
from attrs import define, field
from fastapi import Depends, Query
from morecantile.models import crs_axis_inverted
from rasterio.crs import CRS
from rio_tiler.constants import WGS84_CRS
from rio_tiler.utils import CRS_to_urn
from starlette.requests import Request
from starlette.templating import Jinja2Templates

from titiler.core.factory import FactoryExtension, TilerFactory
from titiler.core.resources.enums import ImageType
from titiler.core.resources.responses import XMLResponse
from titiler.core.utils import (
    rio_crs_to_pyproj,
    tms_limits,
    tms_limits_to_xml,
    tms_to_xml,
)

jinja2_env = jinja2.Environment(
    autoescape=jinja2.select_autoescape(["xml"]),
    loader=jinja2.ChoiceLoader([jinja2.PackageLoader(__package__, "templates")]),
)
DEFAULT_TEMPLATES = Jinja2Templates(env=jinja2_env)


@define
class wmtsExtension(FactoryExtension):
    """WMTS Extension for TilerFactory."""

    # TileMatrixSet to use as Default Layer in the WMTS capabilities document.
    default_tms: str = field(default="WebMercatorQuad")

    # Geographic Coordinate Reference System.
    crs: CRS = field(default=WGS84_CRS)

    templates: Jinja2Templates = field(default=DEFAULT_TEMPLATES)

    def register(self, factory: TilerFactory):  # type: ignore [override] # noqa: C901
        """Register extension's endpoints."""

        @factory.router.get(
            "/WMTSCapabilities.xml",
            response_class=XMLResponse,
            operation_id=f"{factory.operation_prefix}getWMTS",
        )
        def wmts(
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
            reader_params=Depends(factory.reader_dependency),
            tile_params=Depends(factory.tile_dependency),
            layer_params=Depends(factory.layer_dependency),
            dataset_params=Depends(factory.dataset_dependency),
            post_process=Depends(factory.process_dependency),
            colormap=Depends(factory.colormap_dependency),
            render_params=Depends(factory.render_dependency),
            env=Depends(factory.environment_dependency),
        ):
            """OGC WMTS endpoint."""
            qs_key_to_remove = [
                "tile_format",
                "tile_scale",
                "service",
                "use_epsg",
                "request",
            ]
            qs = [
                (key, value)
                for (key, value) in request.query_params._list
                if key.lower() not in qs_key_to_remove
            ]

            with rasterio.Env(**env):
                with factory.reader(src_path, **reader_params.as_dict()) as src_dst:
                    bounds = src_dst.get_geographic_bounds(self.crs)

            tileMatrixSet: list[dict[str, Any]] = []
            for tms_id in factory.supported_tms.list():
                tms = factory.supported_tms.get(tms_id)
                try:
                    with rasterio.Env(**env):
                        with factory.reader(
                            src_path, tms=tms, **reader_params.as_dict()
                        ) as src_dst:
                            tms_minzoom = src_dst.minzoom
                            tms_maxzoom = src_dst.maxzoom

                            _limits = tms_limits(
                                tms,
                                bounds,
                                zooms=(tms_minzoom, tms_maxzoom),
                                geographic_crs=self.crs,
                            )

                    if use_epsg:
                        supported_crs = f"EPSG:{tms.crs.to_epsg()}"
                    else:
                        supported_crs = tms.crs.srs

                    tileMatrixSet.append(
                        {
                            "id": tms_id,
                            "tilematrix": tms_to_xml(tms, tms_minzoom, tms_maxzoom),
                            "crs": supported_crs,
                            "limits": tms_limits_to_xml(_limits),
                        }
                    )
                except Exception as e:  # noqa
                    pass

            bbox_crs_type = "WGS84BoundingBox"
            bbox_crs_uri = "urn:ogc:def:crs:OGC:2:84"
            if self.crs != WGS84_CRS:
                bbox_crs_type = "BoundingBox"
                bbox_crs_uri = CRS_to_urn(self.crs)  # type: ignore
                # WGS88BoundingBox is always xy ordered, but BoundingBox must match the CRS order
                proj_crs = rio_crs_to_pyproj(self.crs)
                if crs_axis_inverted(proj_crs):
                    # match the bounding box coordinate order to the CRS
                    bounds = [bounds[1], bounds[0], bounds[3], bounds[2]]

            layers: list[dict[str, Any]] = []
            for tilematrix in tileMatrixSet:
                route_params = {
                    "z": "{TileMatrix}",
                    "x": "{TileCol}",
                    "y": "{TileRow}",
                    "scale": tile_scale,
                    "format": tile_format.value,
                    "tileMatrixSetId": tilematrix["id"],
                }
                layers.append(
                    {
                        "is_default": tilematrix["id"] == self.default_tms,
                        "title": src_path if isinstance(src_path, str) else "TiTiler",
                        "identifier": tilematrix["id"],
                        "tms_identifier": tilematrix["id"],
                        "limits": tilematrix["limits"],
                        "tiles_url": factory.url_for(request, "tile", **route_params),
                        "query_string": urlencode(qs, doseq=True) if qs else None,
                        "bounds": bounds,
                    }
                )

            return self.templates.TemplateResponse(
                request,
                name="wmts.xml",
                context={
                    "layers": layers,
                    "tileMatrixSets": tileMatrixSet,
                    "bbox_crs_type": bbox_crs_type,
                    "bbox_crs_uri": bbox_crs_uri,
                    "media_type": tile_format.mediatype,
                },
                media_type="application/xml",
            )
