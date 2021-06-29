"""TiTiler MosaicJSON demo endpoints."""

from titiler.application.custom import ColorMapParams
from titiler.mosaic.factory import MosaicTilerFactory

mosaic = MosaicTilerFactory(
    colormap_dependency=ColorMapParams, router_prefix="mosaicjson"
)

router = mosaic.router
