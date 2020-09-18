"""TiTiler STAC Demo endpoint."""

from dataclasses import dataclass
from typing import Callable, Dict, List, Type, Union

import pkg_resources
from rio_tiler_crs import STACReader

from ..dependencies import AssetsParams
from ..models.dataset import Info, Metadata
from .factory import TMSTilerFactory

from fastapi import Depends

from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

template_dir = pkg_resources.resource_filename("titiler", "templates")
templates = Jinja2Templates(directory=template_dir)


@dataclass
class STACTiler(TMSTilerFactory):
    """Custom Tiler Class for STAC."""

    reader: Type[STACReader] = STACReader
    additional_dependency: Callable[[], Dict] = AssetsParams

    # Overwrite _info method to return the list of assets when no assets is passed.
    def _info(self):
        """Register /info endpoint to router."""

        @self.router.get(
            "/info",
            response_model=Union[List[str], Dict[str, Info]],
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={200: {"description": "Return dataset's basic info."}},
        )
        def info(
            src_path=Depends(self.path_dependency),
            kwargs=Depends(self.additional_dependency),
        ):
            """Return basic info."""
            reader = src_path.reader or self.reader
            with reader(src_path.url, **self.reader_options) as src_dst:
                if not kwargs.get("assets"):
                    return src_dst.assets
                info = src_dst.info(**kwargs)
            return info

    # Overwrite _metadata method because the STACTiler output model is different
    # cogMetadata -> Dict[str, cogMetadata]
    def _metadata(self):
        """Register /metadata endpoint to router."""

        @self.router.get(
            "/metadata",
            response_model=Dict[str, Metadata],
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={200: {"description": "Return dataset's metadata."}},
        )
        def metadata(
            src_path=Depends(self.path_dependency),
            metadata_params=Depends(self.metadata_dependency),
            kwargs=Depends(self.additional_dependency),
        ):
            """Return metadata."""
            reader = src_path.reader or self.reader
            with reader(src_path.url, **self.reader_options) as src_dst:
                info = src_dst.metadata(
                    metadata_params.pmin,
                    metadata_params.pmax,
                    **metadata_params.kwargs,
                    **kwargs,
                )
            return info


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
