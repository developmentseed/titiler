"""Titiler mosaic errors."""

from cogeo_mosaic.errors import (
    MosaicAuthError,
    MosaicError,
    MosaicNotFoundError,
    NoAssetFoundError,
)
from rio_tiler.errors import EmptyMosaicError
from starlette import status

MOSAIC_STATUS_CODES = {
    MosaicAuthError: status.HTTP_401_UNAUTHORIZED,
    EmptyMosaicError: status.HTTP_204_NO_CONTENT,
    MosaicNotFoundError: status.HTTP_404_NOT_FOUND,
    NoAssetFoundError: status.HTTP_204_NO_CONTENT,
    MosaicError: status.HTTP_424_FAILED_DEPENDENCY,
}
