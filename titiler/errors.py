"""Titiler error classes."""


class TilerError(Exception):
    """Base exception class."""


class TileNotFoundError(TilerError):
    """Tile not found error."""


class BadRequestError(TilerError):
    """Bad request error."""
