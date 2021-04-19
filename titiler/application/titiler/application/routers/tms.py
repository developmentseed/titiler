"""TiTiler TMS demo endpoints."""

from titiler.application.custom import TileMatrixSetName, TMSParams
from titiler.core.factory import TMSFactory

tms = TMSFactory(supported_tms=TileMatrixSetName, tms_dependency=TMSParams)
router = tms.router  # noqa
