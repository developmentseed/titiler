"""Titiler mosaic errors."""

from rio_tiler.errors import EmptyMosaicError, NoAssetFoundError
from starlette import status

MOSAIC_STATUS_CODES = {
    EmptyMosaicError: status.HTTP_204_NO_CONTENT,
    NoAssetFoundError: status.HTTP_204_NO_CONTENT,
    NotImplementedError: status.HTTP_501_NOT_IMPLEMENTED,
}
