"""OGC Maps API Extension."""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from titiler.core.factory import TilerFactory, FactoryExtension


class Link(BaseModel):
    """Link model."""
    href: str
    rel: str
    type: Optional[str] = None
    title: Optional[str] = None


class Style(BaseModel):
    """OGC Style model."""
    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    links: List[Link] = Field(default_factory=list)


class Map(BaseModel):
    """OGC Map model."""
    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    links: List[Link] = Field(default_factory=list)
    styles: List[Style] = Field(default_factory=list)


class MapList(BaseModel):
    """OGC Maps List model."""
    maps: List[Map] = Field(default_factory=list)
    links: List[Link] = Field(default_factory=list)



class OGCMapsExtension(FactoryExtension):
    """OGC Maps Extension for TiTiler."""

    def register(self, factory: TilerFactory):
        """Register OGC Maps endpoints."""

        @factory.router.get(
            "/maps",
            response_model=MapList,
            response_model_exclude_none=True,
            summary="List available maps",
        )
        def list_maps(request: Request):
            """Return list of available maps."""
            base_url = str(request.base_url)
            
            # For now, treat each dataset as a map
            map_id = "default"  # We could use dataset path/id here
            
            maps = [
                Map(
                    id=map_id,
                    title="Default Map",
                    links=[
                        Link(
                            href=f"{base_url}maps/{map_id}",
                            rel="self",
                            type="application/json",
                        ),
                        Link(
                            href=f"{base_url}maps/{map_id}/styles",
                            rel="styles",
                            type="application/json",
                        ),
                    ],
                )
            ]

            return MapList(
                maps=maps,
                links=[
                    Link(
                        href=f"{base_url}maps",
                        rel="self",
                        type="application/json",
                    )
                ],
            )

        @factory.router.get(
            "/maps/{map_id}",
            response_model=Map,
            response_model_exclude_none=True,
            summary="Get map metadata",
        )
        def get_map(
            request: Request,
            map_id: str,
            src_path=Depends(factory.path_dependency),
        ):
            """Return map metadata."""
            base_url = str(request.base_url)
            
            return Map(
                id=map_id,
                title="Map",
                links=[
                    Link(
                        href=f"{base_url}maps/{map_id}",
                        rel="self",
                        type="application/json",
                    ),
                    Link(
                        href=f"{base_url}maps/{map_id}/styles",
                        rel="styles",
                        type="application/json",
                    ),
                    Link(
                        href=f"{base_url}maps/{map_id}/map",
                        rel="map",
                        type="image/png",
                    ),
                ],
            )

        @factory.router.get(
            "/maps/{map_id}/styles",
            response_model=List[Style],
            response_model_exclude_none=True,
            summary="List available styles",
        )
        def list_styles(
            request: Request,
            map_id: str,
        ):
            """Return list of available styles."""
            base_url = str(request.base_url)
            
            # For now return a default style
            return [
                Style(
                    id="default",
                    title="Default Style",
                    links=[
                        Link(
                            href=f"{base_url}maps/{map_id}/styles/default",
                            rel="self",
                            type="application/json",
                        ),
                    ],
                )
            ]

        @factory.router.get(
            "/maps/{map_id}/map",
            **img_endpoint_params,
            summary="Get map image",
        )
        def get_map_image(
            map_id: str,
            src_path=Depends(factory.path_dependency),
            layer_params=Depends(factory.layer_dependency),
            dataset_params=Depends(factory.dataset_dependency),
            image_params=Depends(factory.img_preview_dependency),
            render_params=Depends(factory.render_dependency),
            colormap=Depends(factory.colormap_dependency),
            env=Depends(factory.environment_dependency),
        ):
            """Return map image."""
            with rasterio.Env(**env):
                with factory.reader(src_path, **reader_params.as_dict()) as src_dst:
                    image = src_dst.preview(
                        **layer_params.as_dict(),
                        **image_params.as_dict(),
                        **dataset_params.as_dict(),
                    )

            content, media_type = render_image(
                image,
                colormap=colormap,
                **render_params.as_dict(),
            )

            return Response(content, media_type=media_type) 