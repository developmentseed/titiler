"""titiler.core.algorithm DEM."""

from typing import Optional

import numpy
from pydantic import Field
from rasterio import windows
from rio_tiler.colormap import apply_cmap, cmap
from rio_tiler.models import ImageData
from rio_tiler.utils import linear_rescale

from titiler.core.algorithm.base import BaseAlgorithm

__all__ = ["HillShade", "Slope", "Contours", "Terrarium", "TerrainRGB"]


class HillShade(BaseAlgorithm):
    """Hillshade."""

    title: str = "Hillshade"
    description: str = "Create hillshade from DEM dataset."

    # parameters
    azimuth: int = Field(45, ge=0, le=360)
    angle_altitude: float = Field(45.0, ge=-90.0, le=90.0)
    buffer: int = Field(3, ge=0, le=99)
    z_exaggeration: float = Field(1.0, ge=1e-6, le=1e6)

    # metadata
    input_nbands: int = 1
    output_nbands: int = 1
    output_dtype: str = "uint8"

    def __call__(self, img: ImageData) -> ImageData:
        """Create hillshade from DEM dataset."""
        x, y = numpy.gradient(img.array[0])
        x *= self.z_exaggeration
        y *= self.z_exaggeration
        slope = numpy.pi / 2.0 - numpy.arctan(numpy.sqrt(x * x + y * y))
        aspect = numpy.arctan2(-x, y)
        azimuth = 360.0 - self.azimuth
        azimuthrad = azimuth * numpy.pi / 180.0
        altituderad = self.angle_altitude * numpy.pi / 180.0
        shaded = numpy.sin(altituderad) * numpy.sin(slope) + numpy.cos(
            altituderad
        ) * numpy.cos(slope) * numpy.cos(azimuthrad - aspect)
        data = 255 * (shaded + 1) / 2
        data[data < 0] = 0  # set hillshade values to min of 0.

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


class Slope(BaseAlgorithm):
    """Slope calculation."""

    title: str = "Slope"
    description: str = "Calculate degrees of slope from DEM dataset."

    # parameters
    buffer: int = Field(3, ge=0, le=99, description="Buffer size for edge effects")
    z_exaggeration: float = Field(1.0, ge=1e-6, le=1e6)

    # metadata
    input_nbands: int = 1
    output_nbands: int = 1
    output_dtype: str = "float32"
    output_min: float = 0
    output_max: float = 90

    def __call__(self, img: ImageData) -> ImageData:
        """Calculate degrees slope from DEM dataset."""
        # Get the pixel size from the transform
        pixel_size_x = abs(img.transform[0])
        pixel_size_y = abs(img.transform[4])

        x, y = numpy.gradient(img.array[0])
        x *= self.z_exaggeration
        y *= self.z_exaggeration
        dx = x / pixel_size_x
        dy = y / pixel_size_y

        slope = numpy.arctan(numpy.sqrt(dx * dx + dy * dy)) * (180 / numpy.pi)

        bounds = img.bounds
        if self.buffer:
            slope = slope[self.buffer : -self.buffer, self.buffer : -self.buffer]

            window = windows.Window(
                col_off=self.buffer,
                row_off=self.buffer,
                width=slope.shape[1],
                height=slope.shape[0],
            )
            bounds = windows.bounds(window, img.transform)

        return ImageData(
            slope.astype(self.output_dtype),
            assets=img.assets,
            crs=img.crs,
            bounds=bounds,
            band_names=["slope"],
        )


class Contours(BaseAlgorithm):
    """Contours.

    Original idea from https://custom-scripts.sentinel-hub.com/dem/contour-lines/
    """

    title: str = "Contours"
    description: str = "Create contours from DEM dataset."

    # parameters
    increment: int = Field(35, ge=0, le=999)
    thickness: int = Field(1, ge=0, le=10)
    minz: int = Field(-12000, ge=-99999, le=99999)
    maxz: int = Field(8000, ge=-99999, le=99999)

    # metadata
    input_nbands: int = 1
    output_nbands: int = 3
    output_dtype: str = "uint8"

    def __call__(self, img: ImageData) -> ImageData:
        """Add contours."""
        data = img.data.astype("float64")

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

    title: str = "Terrarium"
    description: str = "Encode DEM into RGB (Mapzen Terrarium)."
    nodata_height: Optional[float] = Field(None, ge=-99999.0, le=99999.0)

    # metadata
    input_nbands: int = 1
    output_nbands: int = 3
    output_dtype: str = "uint8"

    def __call__(self, img: ImageData) -> ImageData:
        """Encode DEM into RGB."""
        data = numpy.clip(img.array[0] + 32768.0, 0.0, 65535.0)
        if self.nodata_height is not None:
            data[img.array.mask[0]] = numpy.clip(
                self.nodata_height + 32768.0, 0.0, 65535.0
            )
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

    title: str = "TerrainRGB"
    description: str = "Encode DEM into RGB (Mapbox Terrain RGB)."

    # parameters
    interval: float = Field(0.1, ge=0.0, le=1.0)
    baseval: float = Field(-10000.0, ge=-99999.0, le=99999.0)
    nodata_height: Optional[float] = Field(None, ge=-99999.0, le=99999.0)

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

        if self.nodata_height is not None:
            data[img.array.mask[0]] = (
                self.nodata_height - self.baseval
            ) / self.interval

        data_int32 = data.astype(numpy.int32)
        b = (data_int32) & 0xFF
        g = (data_int32 >> 8) & 0xFF
        r = (data_int32 >> 16) & 0xFF

        return ImageData(
            numpy.ma.stack([r, g, b]).astype(self.output_dtype),
            assets=img.assets,
            crs=img.crs,
            bounds=img.bounds,
        )
