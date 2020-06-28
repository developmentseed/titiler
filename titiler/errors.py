"""Titiler error classes."""


class TilerError(Exception):
    """Base exception class."""


class TileNotFoundError(TilerError):
    """Tile not found error."""
