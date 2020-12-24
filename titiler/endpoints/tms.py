"""TMS Api."""

from ..dependencies import TileMatrixSetNames, TMSParams
from .factory import TMSFactory

tms = TMSFactory(supported_tms=TileMatrixSetNames, tms_dependency=TMSParams)
router = tms.router  # noqa
