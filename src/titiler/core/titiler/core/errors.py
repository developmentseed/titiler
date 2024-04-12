"""Titiler error classes."""

from typing import Callable, Dict, Type

from fastapi import FastAPI
from rasterio.errors import RasterioError, RasterioIOError
from rio_tiler.errors import (
    InvalidAssetName,
    InvalidBandName,
    InvalidColorFormat,
    MissingAssets,
    MissingBands,
    RioTilerError,
    TileOutsideBounds,
)
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class TilerError(Exception):
    """Base exception class."""


class TileNotFoundError(TilerError):
    """Tile not found error."""


class BadRequestError(TilerError):
    """Bad request error."""


DEFAULT_STATUS_CODES = {
    BadRequestError: status.HTTP_400_BAD_REQUEST,
    TileOutsideBounds: status.HTTP_404_NOT_FOUND,
    TileNotFoundError: status.HTTP_404_NOT_FOUND,
    RasterioIOError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    MissingBands: status.HTTP_400_BAD_REQUEST,
    MissingAssets: status.HTTP_400_BAD_REQUEST,
    InvalidColorFormat: status.HTTP_400_BAD_REQUEST,
    InvalidAssetName: status.HTTP_404_NOT_FOUND,
    InvalidBandName: status.HTTP_404_NOT_FOUND,
    RasterioError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    RioTilerError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    Exception: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


def exception_handler_factory(status_code: int) -> Callable:
    """
    Create a FastAPI exception handler from a status code.
    """

    def handler(request: Request, exc: Exception):
        if status_code == status.HTTP_204_NO_CONTENT:
            return Response(content=None, status_code=204)

        return JSONResponse(content={"detail": str(exc)}, status_code=status_code)

    return handler


def add_exception_handlers(
    app: FastAPI, status_codes: Dict[Type[Exception], int]
) -> None:
    """
    Add exception handlers to the FastAPI app.
    """
    for (exc, code) in status_codes.items():
        app.add_exception_handler(exc, exception_handler_factory(code))
