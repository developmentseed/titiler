"""Titiler Enums."""

from enum import Enum


class ImageType(str, Enum):
    """Image Type Enums."""

    png = "png"
    npy = "npy"
    tif = "tif"
    jpg = "jpg"
    webp = "webp"
