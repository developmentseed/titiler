"""STAC Render Extension.

Implements support for reading and applying Item level render extension.
See: https://github.com/stac-extensions/render
"""

from typing import Dict, List, Optional
from urllib.parse import urlencode

from attrs import define
from fastapi import Depends, HTTPException, Path, Request
from pydantic import BaseModel
from typing_extensions import Annotated

from titiler.core.factory import FactoryExtension, MultiBaseTilerFactory
from titiler.core.models.OGC import Link
from titiler.core.utils import check_query_params


class RenderItem(BaseModel, extra="allow"):
    """Render item for stac render extension."""

    assets: List[str]
    title: Optional[str] = None
    rescale: Optional[List[Annotated[List[float], 2]]] = None
    nodata: Optional[float] = None
    colormap_name: Optional[str] = None
    colormap: Optional[Dict] = None
    color_formula: Optional[str] = None
    resampling: Optional[str] = None
    expression: Optional[str] = None
    minmax_zoom: Optional[Annotated[List[int], 2]] = None


class RenderItemWithLinks(BaseModel):
    """Same as RenderItem with url and params."""

    params: RenderItem
    links: List[Link]


class RenderItemList(BaseModel):
    """List of Render Items with links."""

    renders: Dict[str, RenderItemWithLinks]
    links: List[Link]


@define
class stacRenderExtension(FactoryExtension):
    """Add /renders endpoint to a STAC TilerFactory."""

    def register(self, factory: MultiBaseTilerFactory):
        """Register endpoint to the tiler factory."""

        def _prepare_render_item(
            render_id: str,
            render: Dict,
            request: Request,
            src_path: str,
        ) -> Dict:
            """Prepare single render item."""
            links = [
                {
                    "href": factory.url_for(
                        request,
                        "STAC Renders metadata",
                        render_id=render_id,
                    )
                    + "?"
                    + urlencode({"url": src_path}),
                    "rel": "self",
                    "type": "application/json",
                    "title": f"STAC Renders metadata for {render_id}",
                }
            ]

            # List of dependencies a `/tile` URL should validate
            # Note: Those dependencies should only require Query() inputs
            tile_dependencies = [
                factory.reader_dependency,
                factory.tile_dependency,
                factory.layer_dependency,
                factory.dataset_dependency,
                factory.process_dependency,
                # Image rendering Dependencies
                factory.colormap_dependency,
                factory.render_dependency,
            ]
            if check_query_params(tile_dependencies, render):
                query_string = urlencode({"url": src_path, **render}, doseq=True)

                links += [
                    {
                        "href": factory.url_for(
                            request,
                            "tilejson",
                            tileMatrixSetId="{tileMatrixSetId}",
                        )
                        + "?"
                        + query_string,
                        "rel": "tilesets-map",
                        "title": f"tilejson file for {render_id}",
                        "templated": True,
                    },
                    {
                        "href": factory.url_for(
                            request,
                            "wmts",
                            tileMatrixSetId="{tileMatrixSetId}",
                        )
                        + "?"
                        + query_string,
                        "rel": "tilesets-map",
                        "title": f"WMTS service for {render_id}",
                        "templated": True,
                    },
                ]

            return {"params": render, "links": links}

        @factory.router.get(
            "/renders",
            response_model=RenderItemList,
            response_model_exclude_none=True,
            name="List STAC Renders metadata",
            operation_id=f"{factory.operation_prefix}getRenderList",
        )
        def render_list(request: Request, src_path=Depends(factory.path_dependency)):
            with factory.reader(src_path) as src:
                renders = src.item.properties.get("renders", {})

            prepared_renders = {
                render_id: _prepare_render_item(render_id, render, request, src_path)
                for render_id, render in renders.items()
            }
            return {
                "renders": prepared_renders,
                "links": [
                    {
                        "href": str(request.url),
                        "rel": "self",
                        "type": "application/json",
                        "title": "List STAC Renders metadata",
                    },
                ],
            }

        @factory.router.get(
            "/renders/{render_id}",
            response_model=RenderItemWithLinks,
            response_model_exclude_none=True,
            name="STAC Renders metadata",
            operation_id=f"{factory.operation_prefix}getRender",
        )
        def render(
            request: Request,
            render_id: str = Path(
                description="render id",
            ),
            src_path=Depends(factory.path_dependency),
        ):
            with factory.reader(src_path) as src:
                renders = src.item.properties.get("renders", {})

            if render_id not in renders:
                raise HTTPException(status_code=404, detail="Render not found")

            return _prepare_render_item(
                render_id,
                renders[render_id],
                request,
                src_path,
            )
