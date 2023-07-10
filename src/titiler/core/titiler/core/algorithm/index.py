"""titiler.core.algorithm Normalized Index."""

from typing import Sequence

import numpy
from rio_tiler.models import ImageData

from titiler.core.algorithm.base import BaseAlgorithm


class NormalizedIndex(BaseAlgorithm):
    """Normalized Difference Index."""

    # metadata
    input_nbands: int = 2
    output_nbands: int = 1
    output_dtype: str = "float32"
    output_min: Sequence[float] = [-1.0]
    output_max: Sequence[float] = [1.0]

    def __call__(self, img: ImageData) -> ImageData:
        """Normalized difference."""
        b1 = img.data[0].astype("float32")
        b2 = img.data[1].astype("float32")

        arr = numpy.where(img.mask, (b2 - b1) / (b2 + b1), 0)
        arr = numpy.ma.MaskedArray(arr, dtype=self.output_dtype)
        arr.mask = img.mask

        bnames = img.band_names
        return ImageData(
            arr,
            assets=img.assets,
            crs=img.crs,
            bounds=img.bounds,
            band_names=[f"({bnames[1]} - {bnames[0]}) / ({bnames[1]} + {bnames[0]})"],
        )
