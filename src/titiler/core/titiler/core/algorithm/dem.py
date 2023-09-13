"""titiler.core.algorithm DEM."""

import numpy
from rasterio import windows
from rio_tiler.colormap import apply_cmap, cmap
from rio_tiler.models import ImageData
from rio_tiler.utils import linear_rescale

from titiler.core.algorithm.base import BaseAlgorithm


class HillShade(BaseAlgorithm):
    """Hillshade."""

    # parameters
    azimuth: int = 90
    angle_altitude: float = 90.0
    buffer: int = 3

    # metadata
    input_nbands: int = 1
    output_nbands: int = 1
    output_dtype: str = "uint8"

    def __call__(self, img: ImageData) -> ImageData:
        """Create hillshade from DEM dataset."""
        x, y = numpy.gradient(img.array[0])
        slope = numpy.pi / 2.0 - numpy.arctan(numpy.sqrt(x * x + y * y))
        aspect = numpy.arctan2(-x, y)
        azimuthrad = self.azimuth * numpy.pi / 180.0
        altituderad = self.angle_altitude * numpy.pi / 180.0
        shaded = numpy.sin(altituderad) * numpy.sin(slope) + numpy.cos(
            altituderad
        ) * numpy.cos(slope) * numpy.cos(azimuthrad - aspect)
        data = 255 * (shaded + 1) / 2

        bounds = img.bounds
        if self.buffer:
            data = data[self.buffer : -self.buffer, self.buffer : -self.buffer]

            window = windows.Window(
                col_off=self.buffer,
                row_off=self.buffer,
                width=data.shape[1],
                height=data.shape[0],
            )
            bounds = windows.bounds(window, img.transform)

        return ImageData(
            data.astype(self.output_dtype),
            assets=img.assets,
            crs=img.crs,
            bounds=bounds,
            band_names=["hillshade"],
        )


class Contours(BaseAlgorithm):
    """Contours.

    Original idea from https://custom-scripts.sentinel-hub.com/dem/contour-lines/
    """

    # parameters
    increment: int = 35
    thickness: int = 1
    minz: int = -12000
    maxz: int = 8000

    # metadata
    input_nbands: int = 1
    output_nbands: int = 3
    output_dtype: str = "uint8"

    def __call__(self, img: ImageData) -> ImageData:
        """Add contours."""
        data = img.data

        # Apply rescaling for minz,maxz to 1->255 and apply Terrain colormap
        arr = linear_rescale(data, (self.minz, self.maxz), (1, 255)).astype(
            self.output_dtype
        )
        arr, _ = apply_cmap(arr, cmap.get("terrain"))

        # set black (0) for contour lines
        arr = numpy.where(data % self.increment < self.thickness, 0, arr)

        data = numpy.ma.MaskedArray(arr)
        data.mask = ~img.mask

        return ImageData(
            data,
            assets=img.assets,
            crs=img.crs,
            bounds=img.bounds,
        )


class Terrarium(BaseAlgorithm):
    """Encode DEM into RGB (Mapzen Terrarium)."""

    # metadata
    input_nbands: int = 1
    output_nbands: int = 3
    output_dtype: str = "uint8"

    def __call__(self, img: ImageData) -> ImageData:
        """Encode DEM into RGB."""
        data = numpy.clip(img.array[0] + 32768.0, 0.0, 65535.0)
        r = data / 256
        g = data % 256
        b = (data * 256) % 256

        return ImageData(
            numpy.ma.stack([r, g, b]).astype(self.output_dtype),
            assets=img.assets,
            crs=img.crs,
            bounds=img.bounds,
        )


class TerrainRGB(BaseAlgorithm):
    """Encode DEM into RGB (Mapbox Terrain RGB)."""

    # parameters
    interval: float = 0.1
    baseval: float = -10000.0

    # metadata
    input_nbands: int = 1
    output_nbands: int = 3
    output_dtype: str = "uint8"

    def __call__(self, img: ImageData) -> ImageData:
        """Encode DEM into RGB (Mapbox Terrain RGB).

        Code from https://github.com/mapbox/rio-rgbify/blob/master/rio_rgbify/encoders.py (MIT)

        """

        def _range_check(datarange):
            """
            Utility to check if data range is outside of precision for 3 digit base 256
            """
            maxrange = 256**3

            return datarange > maxrange

        round_digits = 0

        data = img.array[0].astype(numpy.float64)
        data -= self.baseval
        data /= self.interval

        data = numpy.around(data / 2**round_digits) * 2**round_digits

        datarange = data.max() - data.min()
        if _range_check(datarange):
            raise ValueError(f"Data of {datarange} larger than 256 ** 3")

        r = ((((data // 256) // 256) / 256) - (((data // 256) // 256) // 256)) * 256
        g = (((data // 256) / 256) - ((data // 256) // 256)) * 256
        b = ((data / 256) - (data // 256)) * 256

        return ImageData(
            numpy.ma.stack([r, g, b]).astype(self.output_dtype),
            assets=img.assets,
            crs=img.crs,
            bounds=img.bounds,
        )
