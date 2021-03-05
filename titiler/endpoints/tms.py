"""TMS Api."""

from ..dependencies import TileMatrixSetName, TMSParams
from .factory import TMSFactory

tms = TMSFactory(supported_tms=TileMatrixSetName, tms_dependency=TMSParams)
router = tms.router  # noqa
