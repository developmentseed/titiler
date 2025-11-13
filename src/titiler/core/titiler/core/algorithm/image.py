"""titiler.core.algorithm Images"""

import numpy
from rio_tiler.models import ImageData

from titiler.core.algorithm.base import BaseAlgorithm


class ToGrayScale(BaseAlgorithm):
    """Transform a RGB Image to Grayscale."""

    title: str = "Transform a RGB Image to Grayscale"
    description: str = "Transform a RGB Image to Grayscale using the ITU-R 601-2 luma."

    # metadata
    output_nbands: int = 1

    def __call__(self, img: ImageData) -> ImageData:
        """RGB to L."""
        if img.count < 3:
            raise ValueError(
                f"Cannot apply `grayscale` algorithm on image with {img.count} bands."
            )

        arr = (
            img.array[0] * 299 / 1000
            + img.array[1] * 587 / 1000
            + img.array[2] * 114 / 1000
        )
        return ImageData(
            arr.astype(img.array.dtype),
            assets=img.assets,
            crs=img.crs,
            band_names=["grayscale"],
            bounds=img.bounds,
            cutline_mask=img.cutline_mask,
        )


class ToBitonal(BaseAlgorithm):
    """Transform an Image to Bitonal."""

    title: str = "Transform an Image to Bitonal"
    description: str = "All values larger than 127 are set to 255 (white), all other values to 0 (black)."

    # metadata
    output_nbands: int = 1
    output_dtype: str = "uint8"

    def __call__(self, img: ImageData) -> ImageData:
        """Image to Bitonal"""
        if img.count == 3:
            # Convert to Grayscale
            arr = (
                img.array[0] * 299 / 1000
                + img.array[1] * 587 / 1000
                + img.array[2] * 114 / 1000
            )
        elif img.count == 1:
            arr = img.array
        else:
            raise ValueError(
                f"Cannot apply `bitonal` algorithm on image with {img.count} bands."
            )

        return ImageData(
            numpy.ma.where(arr > 127, 255, 0).astype("uint8"),
            assets=img.assets,
            crs=img.crs,
            bounds=img.bounds,
            band_names=["bitonal"],
            cutline_mask=img.cutline_mask,
        )
