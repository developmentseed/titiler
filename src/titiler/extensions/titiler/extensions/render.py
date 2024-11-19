"""rio-stac render Extension."""

from typing import Dict

from attrs import define
from fastapi import Depends

from titiler.core.factory import FactoryExtension, MultiBaseTilerFactory


@define
class renderExtension(FactoryExtension):
    """Add /render endpoint to a COG TilerFactory."""

    def register(self, factory: MultiBaseTilerFactory):
        """Register endpoint to the tiler factory."""

        @factory.router.get(
            "/renders", response_model=Dict, name="Show STAC item render options"
        )
        def render(src_path=Depends(factory.path_dependency)):
            """Show render options for STAC item."""
            with factory.reader(src_path) as src:
                renders = {}
                if "renders" in src.item.properties:
                    renders = src.item.properties.get("renders")
                return {"renders": renders}
