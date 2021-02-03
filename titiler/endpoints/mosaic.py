"""TiTiler MosaicJSON Demo endpoint."""

from .factory import MosaicTilerFactory

mosaic = MosaicTilerFactory(router_prefix="mosaicjson")

router = mosaic.router
