"""Titiler Enums."""

from enum import Enum


class ImageType(str, Enum):
    """Image Type Enums."""

    png = "png"
    npy = "npy"
    tif = "tif"
    jpg = "jpg"
    webp = "webp"


class ImageMimeTypes(str, Enum):
    """Image MineTypes."""

    geotiff = "image/tiff; application=geotiff"
    tiff = "image/tiff"
    tif = "image/tiff"
    cog = "image/geo+tiff; application=geotiff; profile=cloud-optimized"
    jp2 = "image/jp2"
    png = "image/png"
    jpeg = "image/jpeg"
    jpg = "image/jpeg"
    webp = "image/webp"
    binnary = "application/x-binary"
    npy = "application/x-binary"


class MimeTypes(str, Enum):
    """Responses MineTypes."""

    xml = "application/xml"
    json = "application/json"
    html = "text/html"
    text = "text/plain"
