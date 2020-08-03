"""Titiler Enums."""

from enum import Enum
from types import DynamicClassAttribute

from rio_tiler.mosaic.methods import defaults


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


class NodataTypes(str, Enum):
    """rio-tiler Nodata types."""

    Alpha = "Alpha"
    Mask = "Mask"
    Internal = "Internal"
    Nodata = "Nodata"
    Empty = "None"


class PixelSelectionMethod(str, Enum):
    """rio-tiler-mosaic pixel selection methods"""

    first = "first"
    highest = "highest"
    lowest = "lowest"
    mean = "mean"
    median = "median"
    stdev = "stdev"

    @DynamicClassAttribute
    def method(self):
        """Return rio-tiler-mosaic pixel selection class"""
        return getattr(defaults, f"{self._value_.title()}Method")
