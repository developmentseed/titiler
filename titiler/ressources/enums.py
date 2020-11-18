"""Titiler Enums."""

from enum import Enum
from types import DynamicClassAttribute

from rio_tiler.mosaic.methods import defaults
from rio_tiler.profiles import img_profiles


class MimeTypes(str, Enum):
    """Responses MineTypes."""

    tif = "image/tiff; application=geotiff"
    jp2 = "image/jp2"
    png = "image/png"
    pngraw = "image/png"
    jpeg = "image/jpeg"
    webp = "image/webp"
    npy = "application/x-binary"
    xml = "application/xml"
    json = "application/json"
    html = "text/html"
    text = "text/plain"


class ImageDrivers(str, Enum):
    """Rio-tiler supported output drivers."""

    jpeg = "JPEG"
    png = "PNG"
    pngraw = "PNG"
    tif = "GTiff"
    webp = "WEBP"
    jp2 = "JP2OpenJPEG"
    npy = "NPY"


class ImageType(str, Enum):
    """Available Output image type."""

    png = "png"
    npy = "npy"
    tif = "tif"
    jpeg = "jpg"
    jp2 = "jp2"
    webp = "webp"
    pngraw = "pngraw"

    @DynamicClassAttribute
    def profile(self):
        """Return rio-tiler image default profile."""
        return img_profiles.get(self._name_, {})

    @DynamicClassAttribute
    def driver(self):
        """Return rio-tiler image default profile."""
        return ImageDrivers[self._name_].value

    @DynamicClassAttribute
    def mimetype(self):
        """Return image mimetype."""
        return MimeTypes[self._name_].value


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
