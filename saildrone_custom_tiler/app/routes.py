"""routes.

app/routes.py
"""
from dataclasses import dataclass
from typing import Callable, Dict, Type
from urllib.parse import urlencode

from fastapi import Depends, Path
from starlette.requests import Request
from starlette.responses import Response

from morecantile import TileMatrixSet
from rio_tiler.io import BaseReader, COGReader

from titiler.core.factory import BaseTilerFactory, img_endpoint_params
from titiler.core.dependencies import DefaultDependency, ImageParams, MetadataParams, TMSParams
from titiler.core.models.mapbox import TileJSON
from titiler.core.resources.enums import ImageType

from .cache import cached


@dataclass
class TilerFactory(BaseTilerFactory):

    # Default reader is set to COGReader
    reader: Type[BaseReader] = COGReader

    # Endpoint Dependencies
    img_dependency: Type[DefaultDependency] = ImageParams

    # TileMatrixSet dependency
    tms_dependency: Callable[..., TileMatrixSet] = TMSParams

    def register_routes(self):
        """This Method register routes to the router."""
        self.tile()
        self.tilejson()

    def tile(self):
        """Register /tiles endpoint."""

        @self.router.get(r"/tiles/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}", **img_endpoint_params)
        @cached()
        def tile(
            z: int = Path(..., ge=0, le=30, description="TMS tiles's zoom level"),
            x: int = Path(..., description="TMS tiles's column"),
            y: int = Path(..., description="TMS tiles's row"),
            tms: TileMatrixSet = Depends(self.tms_dependency),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            render_params=Depends(self.render_dependency),
            postprocess_params=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
        ):
            """Create map tile from a dataset."""
            with self.reader(src_path, tms=tms) as src_dst:
                data = src_dst.tile(
                    x,
                    y,
                    z,
                    **layer_params,
                    **dataset_params,
                )
                dst_colormap = getattr(src_dst, "colormap", None)

            format = ImageType.jpeg if data.mask.all() else ImageType.png

            image = data.post_process(**postprocess_params)

            content = image.render(
                img_format=format.driver,
                colormap=colormap or dst_colormap,
                **format.profile,
                **render_params,
            )

            return Response(content, media_type=format.mediatype)

    def tilejson(self):
        """Register /tilejson.json endpoint."""

        @self.router.get(
            "/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        @self.router.get(
            "/{TileMatrixSetId}/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        @cached()
        def tilejson(
            request: Request,
            tms: TileMatrixSet = Depends(self.tms_dependency),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            render_params=Depends(self.render_dependency),
            postprocess_params=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
        ):
            """Return TileJSON document for a dataset."""
            route_params = {
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
                "TileMatrixSetId": tms.identifier,
            }
            tiles_url = self.url_for(request, "tile", **route_params)

            qs_key_to_remove = [
                "tilematrixsetid",
                "tile_format",
                "tile_scale",
                "minzoom",
                "maxzoom",
            ]
            qs = [
                (key, value)
                for (key, value) in request.query_params._list
                if key.lower() not in qs_key_to_remove
            ]
            if qs:
                tiles_url += f"?{urlencode(qs)}"

            with self.reader(src_path, tms=tms) as src_dst:
                return {
                    "bounds": src_dst.geographic_bounds,
                    "minzoom": src_dst.minzoom,
                    "maxzoom": src_dst.maxzoom,
                    "name": "cogeotif",
                    "tiles": [tiles_url],
                }


cog = TilerFactory()
