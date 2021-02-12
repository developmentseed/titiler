"""TiTiler STAC Demo endpoint."""

from dataclasses import dataclass
from typing import Dict, List, Type, Union

import rasterio
from geojson_pydantic.features import Feature
from rio_tiler.io import STACReader
from rio_tiler.models import Info, Metadata

from .. import utils
from ..dependencies import AssetsBidxExprParams, AssetsBidxParams
from ..resources.responses import GeoJSONResponse
from ..templates import templates
from .factory import TilerFactory

from fastapi import Depends

from starlette.requests import Request
from starlette.responses import HTMLResponse


@dataclass
class STACTiler(TilerFactory):
    """Custom Tiler Class for STAC.

    Note:
        To be able to use the rio_tiler.io.STACReader we need to be able to pass a `assets`
        argument to most of its methods. By using the `AssetsBidxExprParams` for the `layer_dependency`, the
        .tile(), .point(), .preview() and the .part() methods will receive assets, expression or indexes arguments.

        The rio_tiler.io.STACReader  `.info()` and `.metadata()` have `assets` as
        a requirement arguments (https://github.com/cogeotiff/rio-tiler/blob/master/rio_tiler/io/base.py#L365).
        This means we have to update the /info and /metadata endpoints in order to add the `assets` dependency.

    """

    reader: Type[STACReader] = STACReader

    # Assets,Indexes/Expression Dependencies
    layer_dependency: Type[AssetsBidxExprParams] = AssetsBidxExprParams

    # Overwrite _info method to return the list of assets when no assets is passed.
    def info(self):
        """Register /info endpoint."""

        @self.router.get(
            "/info",
            response_model=Union[List[str], Dict[str, Info]],
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={200: {"description": "Return dataset's basic info."}},
        )
        def info(
            src_path=Depends(self.path_dependency),
            asset_params=Depends(AssetsBidxParams),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Return basic info."""
            with rasterio.Env(**self.gdal_config):
                with self.reader(src_path.url, **self.reader_options) as src_dst:
                    if not asset_params.assets:
                        return src_dst.assets
                    return src_dst.info(**asset_params.kwargs, **kwargs)

        @self.router.get(
            "/info.geojson",
            response_model=Feature,
            response_model_exclude_none=True,
            response_class=GeoJSONResponse,
            responses={
                200: {
                    "content": {"application/geo+json": {}},
                    "description": "Return dataset's basic info as a GeoJSON feature.",
                }
            },
        )
        def info_geojson(
            src_path=Depends(self.path_dependency),
            asset_params=Depends(AssetsBidxParams),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Return dataset's basic info as a GeoJSON feature."""
            with rasterio.Env(**self.gdal_config):
                with self.reader(src_path.url, **self.reader_options) as src_dst:
                    if not asset_params.assets:
                        info = {"available_assets": src_dst.assets}
                    else:
                        info = {"dataset": src_path.url}
                        info["assets"] = {
                            asset: meta.dict(exclude_none=True)
                            for asset, meta in src_dst.info(
                                **asset_params.kwargs, **kwargs
                            ).items()
                        }
                    geojson = utils.bbox_to_feature(src_dst.bounds, properties=info)

            return geojson

    # Overwrite _metadata method because the STACTiler output model is different
    # cogMetadata -> Dict[str, cogMetadata]
    def metadata(self):
        """Register /metadata endpoint."""

        @self.router.get(
            "/metadata",
            response_model=Dict[str, Metadata],
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={200: {"description": "Return dataset's metadata."}},
        )
        def metadata(
            src_path=Depends(self.path_dependency),
            asset_params=Depends(AssetsBidxParams),
            metadata_params=Depends(self.metadata_dependency),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Return metadata."""
            with rasterio.Env(**self.gdal_config):
                with self.reader(src_path.url, **self.reader_options) as src_dst:
                    return src_dst.metadata(
                        metadata_params.pmin,
                        metadata_params.pmax,
                        **asset_params.kwargs,
                        **metadata_params.kwargs,
                        **kwargs,
                    )


stac = STACTiler(router_prefix="stac")


@stac.router.get("/viewer", response_class=HTMLResponse)
def stac_demo(request: Request):
    """STAC Viewer."""
    return templates.TemplateResponse(
        name="stac_index.html",
        context={
            "request": request,
            "tilejson": stac.url_for(request, "tilejson"),
            "metadata": stac.url_for(request, "info"),
        },
        media_type="text/html",
    )


router = stac.router
