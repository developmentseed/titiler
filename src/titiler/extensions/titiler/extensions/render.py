"""render Extension."""

from pprint import pprint
from typing import Dict, List, Optional
from urllib.parse import urlencode

from attrs import define
from fastapi import Depends, HTTPException, Path, Request
from fastapi.dependencies.utils import get_dependant, request_params_to_args
from pydantic import BaseModel
from typing_extensions import Annotated

from titiler.core.factory import FactoryExtension, MultiBaseTilerFactory
from titiler.core.models.OGC import Link


class RenderItem(BaseModel, extra="allow"):
    """Render item for stac render extension."""

    assets: List[str]
    title: Optional[str] = None
    rescale: Optional[list[Annotated[List[float], 2]]] = None
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
class renderExtension(FactoryExtension):
    """Add /renders endpoint to a STAC TilerFactory."""

    def register(self, factory: MultiBaseTilerFactory):
        """Register endpoint to the tiler factory."""

        def _prepare_query_string(render: Dict, src_path: str) -> str:
            # List of dependencies a `/tile` URL should validate
            # Note: Those dependencies should only require Query() inputs
            tile_dependencies = [
                factory.layer_dependency,
                factory.dataset_dependency,
                # Image rendering Dependencies
                factory.rescale_dependency,
                factory.color_formula_dependency,
                factory.colormap_dependency,
                factory.render_dependency,
            ]

            query = {"url": src_path}
            for dependency in tile_dependencies:
                dep = get_dependant(path="", call=dependency)
                if dep.query_params:
                    # call the dependency with the query-parameters values
                    query_values, _errors = request_params_to_args(
                        dep.query_params, render
                    )
                    _ = dependency(**query_values)
                    query.update(query_values)
            return urlencode(
                {key: value for key, value in query.items() if value is not None},
                doseq=True,
            )

        def _prepare_render_item(
            render_id: str, render: Dict, request: Request, src_path: str
        ) -> Dict:
            # url = factory.url_for(request, "tile", tileMatrixSetId="{tileMatrixSetId}")

            query_string = _prepare_query_string(render, src_path)
            links = [
                {
                    "href": factory.url_for(
                        request,
                        "Show STAC render",
                        render_id=render_id,
                    )
                    + "?"
                    + urlencode({"url": src_path}),
                    "rel": "self",
                    "type": "application/json",
                    "title": f"{render_id} render item",
                },
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

            return {
                "params": render,
                "links": links,
            }

        @factory.router.get(
            "/renders",
            response_model=RenderItemList,
            response_model_exclude_none=True,
            name="List STAC renders",
        )
        def render_list(request: Request, src_path=Depends(factory.path_dependency)):
            with factory.reader(src_path) as src:
                renders = src.item.properties.get("renders", {})
            pprint(renders)
            prepared_renders = {
                render_id: _prepare_render_item(render_id, render, request, src_path)
                for render_id, render in renders.items()
            }
            pprint(prepared_renders)
            return {
                "renders": prepared_renders,
                "links": [
                    {
                        "href": str(request.url),
                        "rel": "self",
                        "type": "application/json",
                        "title": "List Render Items",
                    },
                ],
            }

        @factory.router.get(
            "/renders/{render_id}",
            response_model=RenderItemWithLinks,
            response_model_exclude_none=True,
            name="Show STAC render",
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
                render = renders[render_id]

                return _prepare_render_item(render_id, render, request, src_path)
