"""TiTiler MosaicJSON demo endpoints."""

from titiler.application.custom import ColorMapParams
from titiler.core.factory import MosaicTilerFactory

mosaic = MosaicTilerFactory(
    colormap_dependency=ColorMapParams, router_prefix="mosaicjson"
)

router = mosaic.router
