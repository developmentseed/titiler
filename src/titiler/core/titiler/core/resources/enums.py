"""Titiler.core Enums."""

from enum import Enum
from types import DynamicClassAttribute

from rio_tiler.profiles import img_profiles


class MediaType(str, Enum):
    """Responses Media types formerly known as MIME types."""

    tif = "image/tiff; application=geotiff"
    tiff = "image/tiff; application=geotiff"
    jp2 = "image/jp2"
    png = "image/png"
    pngraw = "image/png"
    jpeg = "image/jpeg"
    jpg = "image/jpg"
    webp = "image/webp"
    npy = "application/x-binary"
    xml = "application/xml"
    json = "application/json"
    geojson = "application/geo+json"
    html = "text/html"
    text = "text/plain"
    pbf = "application/x-protobuf"
    mvt = "application/vnd.mapbox-vector-tile"
    ndjson = "application/ndjson"
    geojsonseq = "application/geo+json-seq"
    schemajson = "application/schema+json"
    csv = "text/csv"
    openapi30_json = "application/vnd.oai.openapi+json;version=3.0"
    openapi30_yaml = "application/vnd.oai.openapi;version=3.0"
    gif = "image/gif"


class ImageDriver(str, Enum):
    """Supported output GDAL drivers."""

    jpeg = "JPEG"
    jpg = "JPEG"
    png = "PNG"
    pngraw = "PNG"
    tif = "GTiff"
    tiff = "GTiff"
    webp = "WEBP"
    jp2 = "JP2OpenJPEG"
    npy = "NPY"
    gif = "GIF"


class ImageType(str, Enum):
    """Available Output image type."""

    png = "png"
    npy = "npy"
    tif = "tif"
    tiff = "tiff"
    jpeg = "jpeg"
    jpg = "jpg"
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
        return ImageDriver[self._name_].value

    @DynamicClassAttribute
    def mediatype(self):
        """Return image media type."""
        return MediaType[self._name_].value


class OptionalHeader(str, Enum):
    """Optional Header to add in responses."""

    server_timing = "Server-Timing"
    x_assets = "X-Assets"
