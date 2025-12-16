"""STAC Render Extension.

Implements support for reading and applying Item level render extension.
See: https://github.com/stac-extensions/render
"""

from typing import Annotated, Any
from urllib.parse import urlencode

from attrs import define
from fastapi import Depends, HTTPException, Path, Request
from pydantic import BaseModel
from starlette.routing import NoMatchFound

from titiler.core.factory import FactoryExtension, MultiBaseTilerFactory
from titiler.core.models.OGC import Link
from titiler.core.utils import check_query_params


class RenderItem(BaseModel, extra="allow"):
    """Render item for stac render extension."""

    assets: list[str]
    title: str | None = None
    rescale: list[Annotated[list[float], 2]] | None = None
    nodata: float | None = None
    colormap_name: str | None = None
    colormap: dict | None = None
    color_formula: str | None = None
    resampling: str | None = None
    expression: str | None = None
    minmax_zoom: Annotated[list[int], 2] | None = None


class RenderItemWithLinks(BaseModel):
    """Same as RenderItem with url and params."""

    params: RenderItem
    links: list[Link]


class RenderItemList(BaseModel):
    """List of Render Items with links."""

    renders: dict[str, RenderItemWithLinks]
    links: list[Link]


@define
class stacRenderExtension(FactoryExtension):
    """Add /renders endpoint to a STAC TilerFactory."""

    def register(self, factory: MultiBaseTilerFactory):  # type: ignore [override]
        """Register endpoint to the tiler factory."""

        def _prepare_render_item(
            render_id: str,
            render: dict,
            request: Request,
            src_path: str,
        ) -> dict:
            """Prepare single render item."""
            links: list[dict[str, Any]] = [
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
            if check_query_params(tile_dependencies, render):  # type: ignore[arg-type]
                query_string = urlencode({"url": src_path, **render}, doseq=True)

                links.append(
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
                    }
                )
                try:
                    links.append(
                        {
                            "href": factory.url_for(
                                request,
                                "wmts",
                            )
                            + "?"
                            + query_string,
                            "rel": "tilesets-map",
                            "title": f"WMTS service for {render_id}",
                            "templated": True,
                        },
                    )
                except NoMatchFound:
                    pass

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
