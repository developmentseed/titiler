"""titiler.core.algorithm Ops."""

from typing import Sequence

import numpy
from rio_tiler.models import ImageData

from titiler.core.algorithm.base import BaseAlgorithm

__all__ = ["CastToInt", "Ceil", "Floor"]


class CastToInt(BaseAlgorithm):
    """Cast data to Integer."""

    title: str = "Cast data to Integer"
    description: str = "Cast data to Integer."

    # metadata
    output_dtype: str = "uint8"
    output_min: Sequence[int] = [0]
    output_max: Sequence[int] = [255]

    def __call__(self, img: ImageData) -> ImageData:
        """Cast Data."""
        return ImageData(
            img.array.astype("uint8"),
            assets=img.assets,
            crs=img.crs,
            bounds=img.bounds,
            band_names=img.band_names,
            metadata=img.metadata,
            cutline_mask=img.cutline_mask,
        )


class Ceil(BaseAlgorithm):
    """Round data to the smallest integer."""

    title: str = "Round data to the smallest integer"
    description: str = "Round data to the smallest integer."

    # metadata
    output_dtype: str = "uint8"
    output_min: Sequence[int] = [0]
    output_max: Sequence[int] = [255]

    def __call__(self, img: ImageData) -> ImageData:
        """Cast Data."""
        return ImageData(
            numpy.ceil(img.array).astype("uint8"),
            assets=img.assets,
            crs=img.crs,
            bounds=img.bounds,
            band_names=img.band_names,
            metadata=img.metadata,
            cutline_mask=img.cutline_mask,
        )


class Floor(BaseAlgorithm):
    """Round data to the largest integer."""

    title: str = "Round data to the largest integer"
    description: str = "Round data to the largest integer."

    # metadata
    output_dtype: str = "uint8"
    output_min: Sequence[int] = [0]
    output_max: Sequence[int] = [255]

    def __call__(self, img: ImageData) -> ImageData:
        """Cast Data."""
        return ImageData(
            numpy.floor(img.array).astype("uint8"),
            assets=img.assets,
            crs=img.crs,
            bounds=img.bounds,
            band_names=img.band_names,
            metadata=img.metadata,
            cutline_mask=img.cutline_mask,
        )
