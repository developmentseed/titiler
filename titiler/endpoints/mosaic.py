"""TiTiler MosaicJSON Demo endpoint."""

from cogeo_mosaic.mosaic import MosaicJSON

from .factory import MosaicTilerFactory

mosaic = MosaicTilerFactory(router_prefix="mosaicjson")


@mosaic.router.post("/validate")
def mosaic_validate(body: MosaicJSON):
    """Validate a MosaicJSON"""
    return True


router = mosaic.router
