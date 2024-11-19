"""render Extension."""

from typing import Any, Dict, List, Literal, Optional

from attrs import define
from fastapi import Depends

from titiler.core.factory import FactoryExtension, MultiBaseTilerFactory

import pystac


@define
class renderExtension(FactoryExtension):
    """Add /stac endpoint to a COG TilerFactory."""

    '''
    '''
    def register(self, factory: MultiBaseTilerFactory):
        """Register endpoint to the tiler factory."""

        @factory.router.get("/renders", response_model=Dict, name="List STAC renders")
        def show_renders(
            src_path=Depends(factory.path_dependency)
        ): 
            with factory.reader(src_path) as src:
                renders = {}
                # if hasattr(src.item, "ext") and src.item.ext.has("renders"):
                #     renders = src.item.ext.renders
                    
                if src.item.properties.get("renders"):
                    renders = src.item.properties.get("renders")
                
                return {"renders": renders}