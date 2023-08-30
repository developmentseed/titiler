"""titiler.core utilities."""

import warnings
from typing import Any, Optional, Sequence, Tuple, Union

import numpy
from rasterio.dtypes import dtype_ranges
from rio_tiler.colormap import apply_cmap
from rio_tiler.errors import InvalidDatatypeWarning
from rio_tiler.models import ImageData
from rio_tiler.types import ColorMapType, IntervalTuple
from rio_tiler.utils import linear_rescale, render

from titiler.core.resources.enums import ImageType


def rescale_array(
    array: numpy.ndarray,
    mask: numpy.ndarray,
    in_range: Sequence[IntervalTuple],
    out_range: Sequence[IntervalTuple] = ((0, 255),),
    out_dtype: Union[str, numpy.number] = "uint8",
) -> numpy.ndarray:
    """Rescale data array"""
    if len(array.shape) < 3:
        array = numpy.expand_dims(array, axis=0)

    nbands = array.shape[0]
    if len(in_range) != nbands:
        in_range = ((in_range[0]),) * nbands

    if len(out_range) != nbands:
        out_range = ((out_range[0]),) * nbands

    for bdx in range(nbands):
        array[bdx] = numpy.where(
            mask[bdx],
            linear_rescale(
                array[bdx], in_range=in_range[bdx], out_range=out_range[bdx]
            ),
            0,
        )

    return array.astype(out_dtype)


def render_image(
    image: ImageData,
    output_format: Optional[ImageType] = None,
    colormap: Optional[ColorMapType] = None,
    add_mask: bool = True,
    **kwargs: Any,
) -> Tuple[bytes, str]:
    """convert image data to file.

    This is adapted from https://github.com/cogeotiff/rio-tiler/blob/066878704f841a332a53027b74f7e0a97f10f4b2/rio_tiler/models.py#L698-L764
    """
    data, mask = image.data.copy(), image.mask.copy()
    datatype_range = image.dataset_statistics or (dtype_ranges[str(data.dtype)],)

    if colormap:
        data, alpha_from_cmap = apply_cmap(data, colormap)
        # Combine both Mask from dataset and Alpha band from Colormap
        mask = numpy.bitwise_and(alpha_from_cmap, mask)
        datatype_range = (dtype_ranges[str(data.dtype)],)

    # If output_format is not set, we choose between JPEG and PNG
    if not output_format:
        output_format = ImageType.jpeg if mask.all() else ImageType.png

    if output_format == ImageType.png and data.dtype not in ["uint8", "uint16"]:
        warnings.warn(
            f"Invalid type: `{data.dtype}` for the `{output_format}` driver. Data will be rescaled using min/max type bounds or dataset_statistics.",
            InvalidDatatypeWarning,
        )
        data = rescale_array(data, mask, in_range=datatype_range)

    elif output_format in [
        ImageType.jpeg,
        ImageType.jpg,
        ImageType.webp,
    ] and data.dtype not in ["uint8"]:
        warnings.warn(
            f"Invalid type: `{data.dtype}` for the `{output_format}` driver. Data will be rescaled using min/max type bounds or dataset_statistics.",
            InvalidDatatypeWarning,
        )
        data = rescale_array(data, mask, in_range=datatype_range)

    elif output_format == ImageType.jp2 and data.dtype not in [
        "uint8",
        "int16",
        "uint16",
    ]:
        warnings.warn(
            f"Invalid type: `{data.dtype}` for the `{output_format}` driver. Data will be rescaled using min/max type bounds or dataset_statistics.",
            InvalidDatatypeWarning,
        )
        data = rescale_array(data, mask, in_range=datatype_range)

    creation_options = {**kwargs, **output_format.profile}
    if output_format == ImageType.tif:
        if "transform" not in creation_options:
            creation_options.update({"transform": image.transform})
        if "crs" not in creation_options and image.crs:
            creation_options.update({"crs": image.crs})

    if not add_mask:
        mask = None

    return (
        render(
            data,
            mask,
            img_format=output_format.driver,
            **creation_options,
        ),
        output_format.mediatype,
    )
