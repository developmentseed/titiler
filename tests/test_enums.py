"""test titiler enums."""

import pytest
from rio_tiler.profiles import img_profiles

from titiler.resources.enums import ImageType


@pytest.mark.parametrize(
    "value,driver,mimetype",
    [
        ("png", "PNG", "image/png"),
        ("npy", "NPY", "application/x-binary"),
        ("tif", "GTiff", "image/tiff; application=geotiff"),
        ("jpeg", "JPEG", "image/jpeg"),
        ("jp2", "JP2OpenJPEG", "image/jp2"),
        ("webp", "WEBP", "image/webp"),
        ("pngraw", "PNG", "image/png"),
    ],
)
def test_imagetype(value, driver, mimetype):
    """Test driver and mimetype values."""
    assert ImageType[value].driver == driver
    assert ImageType[value].mimetype == mimetype


def test_imageprofile():
    """test image profile."""
    ImageType.png.profile == img_profiles.get("png")
    ImageType.pngraw.profile == img_profiles.get("pngraw")
    ImageType.jpeg.profile == img_profiles.get("jpeg")
    ImageType.webp.profile == img_profiles.get("webp")
