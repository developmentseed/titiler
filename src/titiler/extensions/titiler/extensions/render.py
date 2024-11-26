"""render Extension."""

from pprint import pprint
from typing import Annotated, Dict, List, Optional
from urllib.parse import urlencode

from attrs import define
from fastapi import Depends, HTTPException, Path, Request
from fastapi.dependencies.utils import get_dependant, request_params_to_args
from pydantic import BaseModel, RootModel

from titiler.core.factory import FactoryExtension, MultiBaseTilerFactory


class RenderItem(BaseModel):
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


RenderItemList = RootModel[Dict[str, RenderItem]]


class RenderItemWithLink(RenderItem):
    """Same as RenderItem with url and params."""

    url: str
    params: str


@define
class renderExtension(FactoryExtension):
    """Add /renders endpoint to a STAC TilerFactory."""

    def register(self, factory: MultiBaseTilerFactory):
        """Register endpoint to the tiler factory."""

        @factory.router.get(
            "/renders",
            response_model=RenderItemList,
            response_model_exclude_none=True,
            name="List STAC renders",
        )
        def render_list(src_path=Depends(factory.path_dependency)):
            with factory.reader(src_path) as src:
                renders = src.item.properties.get("renders", {})
            pprint(renders)
            return renders

        @factory.router.get(
            "/renders/{render_id}",
            response_model=RenderItemWithLink,
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

                url_params = {
                    "tileMatrixSetId": "{tileMatrixSetId}",
                    "z": "{z}",
                    "x": "{x}",
                    "y": "{y}",
                }

                url = factory.url_for(request, "tile", **url_params)

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

                final_query = {
                    "url": src_path,
                }
                for dependency in tile_dependencies:
                    dep = get_dependant(path="", call=dependency)
                    if dep.query_params:
                        # call the dependency with the query-parameters values
                        query_values, errors = request_params_to_args(
                            dep.query_params, render
                        )
                        _ = dependency(**query_values)
                        final_query.update(query_values)

                return {
                    **render,
                    "url": str(url),
                    "params": urlencode(
                        {
                            key: value
                            for key, value in final_query.items()
                            if value is not None
                        },
                        doseq=True,
                    ),
                }
