"""test titiler rendering function."""

import warnings

import numpy
import pytest
from rasterio.io import MemoryFile
from rio_tiler.errors import InvalidDatatypeWarning
from rio_tiler.models import ImageData

from titiler.core.resources.enums import ImageType
from titiler.core.utils import render_image


def test_rendering():
    """test rendering."""
    im = ImageData(numpy.zeros((1, 256, 256), dtype="uint8"))

    # Should render as JPEG
    content, media = render_image(im)
    assert media == "image/jpeg"
    with MemoryFile(content) as mem:
        with mem.open() as dst:
            assert dst.profile["driver"] == "JPEG"
            assert dst.count == 1
            assert dst.width == 256
            assert dst.height == 256
            arr = dst.read()
            assert numpy.unique(arr).tolist() == [0]

    # Should render as PNG
    content, media = render_image(im, output_format=ImageType.png)
    assert media == "image/png"
    with MemoryFile(content) as mem:
        with mem.open() as dst:
            assert dst.profile["driver"] == "PNG"
            assert dst.count == 2
            arr = dst.read()
            assert numpy.unique(arr[0]).tolist() == [0]

    with pytest.warns(InvalidDatatypeWarning):
        _, media = render_image(
            ImageData(numpy.zeros((1, 256, 256), dtype="uint16")),
            output_format=ImageType.jpeg,
        )
        assert media == "image/jpeg"

    with pytest.warns(InvalidDatatypeWarning):
        _, media = render_image(
            ImageData(numpy.zeros((1, 256, 256), dtype="float32")),
            output_format=ImageType.png,
        )
        assert media == "image/png"

    with pytest.warns(InvalidDatatypeWarning):
        _, media = render_image(
            ImageData(numpy.zeros((1, 256, 256), dtype="float32")),
            output_format=ImageType.jp2,
        )
        assert media == "image/jp2"

    # Make sure that we do not rescale uint16 data when there is a colormap
    # Because the colormap will result in data between 0 and 255 it should be of type uint8
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        cm = {1: (0, 0, 0, 255), 1000: (255, 255, 255, 255)}
        d = numpy.zeros((1, 256, 256), dtype="float32") + 1
        d[0, 0:10, 0:10] = 1000
        content, media = render_image(
            ImageData(d),
            output_format=ImageType.jpeg,
            colormap=cm,
        )
        assert media == "image/jpeg"

    with MemoryFile(content) as mem:
        with mem.open() as dst:
            assert dst.count == 3
            assert dst.dtypes == ("uint8", "uint8", "uint8")
            assert dst.read()[:, 0, 0].tolist() == [255, 255, 255]
            assert dst.read()[:, 11, 11].tolist() == [0, 0, 0]

    # Partial alpha values
    cm = {
        1: (0, 0, 0, 0),
        500: (100, 100, 100, 50),
        1000: (255, 255, 255, 255),
    }
    d = numpy.ma.zeros((1, 256, 256), dtype="float32") + 1
    d[0, 0:10, 0:10] = 500
    d[0, 10:20, 10:20] = 1000
    content, media = render_image(
        ImageData(d),
        output_format=ImageType.png,
        colormap=cm,
    )
    assert media == "image/png"

    with MemoryFile(content) as mem:
        with mem.open() as dst:
            assert dst.count == 4
            assert dst.dtypes == ("uint8", "uint8", "uint8", "uint8")
            assert dst.read()[:, 0, 0].tolist() == [100, 100, 100, 50]
            assert dst.read()[:, 11, 11].tolist() == [255, 255, 255, 255]
            assert dst.read()[:, 30, 30].tolist() == [0, 0, 0, 0]
