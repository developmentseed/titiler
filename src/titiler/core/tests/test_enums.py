"""test titiler enums."""

import pytest
from rio_tiler.profiles import img_profiles

from titiler.core.resources.enums import ImageType


@pytest.mark.parametrize(
    "value,driver,mediatype",
    [
        ("png", "PNG", "image/png"),
        ("npy", "NPY", "application/x-binary"),
        ("tif", "GTiff", "image/tiff; application=geotiff"),
        ("jpg", "JPEG", "image/jpg"),
        ("jpeg", "JPEG", "image/jpeg"),
        ("jp2", "JP2OpenJPEG", "image/jp2"),
        ("webp", "WEBP", "image/webp"),
        ("pngraw", "PNG", "image/png"),
    ],
)
def test_imagetype(value, driver, mediatype):
    """Test driver and mediatype values."""
    assert ImageType[value].driver == driver
    assert ImageType[value].mediatype == mediatype


@pytest.mark.parametrize(
    "driver",
    ["png", "pngraw", "jpg", "jpeg", "webp"],
)
def test_imageprofile(driver):
    """test image profile."""
    assert ImageType[driver].profile == img_profiles.get(driver)
