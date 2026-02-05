"""Dependency validations."""

import re
from json import JSONDecodeError, loads
from typing import Final

from rasterio.crs import CRS

parseable_float_regex: Final[str] = r"\s*(-)?\d+((\.\d+)(e\d+)?)?\s*"


def validate_rescale(rescale_strs: list[str]) -> list[str]:
    """
    Verify that rescale input matches an accepted pattern.
    :param rescale_strs: Caller-provided rescale values.
    :type rescale_strs: list[str]
    :return: Caller-provided rescale values if validated, otherwise an exception is raised.
    :rtype: list[str]
    """
    validated_rescales: list[str] = []
    for rescale_str in rescale_strs:
        error_text = "invalid rescale format"
        rescale_parts = [
            re.sub(r"[\[|\]]", "", part) for part in rescale_str.split(",")
        ]
        if len(rescale_parts) == 2:
            try:
                # Regex validation adds risk, given the different string
                # formats that can be parsed to float, so simply attempt
                # to parse.
                min = float(rescale_parts[0])
                max = float(rescale_parts[1])
            except ValueError as e:
                error_text = f"{error_text}: {e}"
            else:
                validated_rescales.append(f"{min},{max}")
                continue
        raise ValueError(error_text)
    return validated_rescales


def validate_crs(crs_str: str | None) -> str | None:
    """
    Verify that crs input matches an accepted format.
    :param crs_str: Caller-provided crs value.
    :type crs_str: str | None
    :return: Caller-provided crs value if accepted, otherwise an exception is raised.
    :rtype: str | None
    """
    if crs_str is None:
        return None
    if crs_str.startswith("[") and crs_str.endswith(
        "]"
    ):  # this block lifted from OGCMapsParams
        crs_str = crs_str[1:-1]
    try:
        # CRS does not provide a static `is_valid` check, and "many different kinds" of formats
        # are supported, making regex impractical.
        # (https://rasterio.readthedocs.io/en/latest/api/rasterio.crs.html#rasterio.crs.CRS.from_user_input)
        CRS.from_user_input(crs_str)
    except ValueError as e:
        raise ValueError("invalid CRS format") from e
    else:
        return crs_str


def validate_json(json_str: str | None) -> str | None:
    """
    Verify that json input can be parsed.
    :param json_str: Caller-provided crs value.
    :type json_str: str | None
    :return: Caller-provided json_str value if valid, otherwise an exception is raised.
    :rtype: str | None
    """
    if json_str is None:
        return None
    try:
        loads(json_str)
    except JSONDecodeError as e:
        raise ValueError("invalid JSON content") from e
    else:
        return json_str


def validate_bbox(bbox_str: str | None) -> str | None:
    """
    Verify that bbox can be parsed.
    :param bbox_str: Caller-provided bbox value.
    :type bbox_str: str | None
    :return: Caller-provided bbox_str value if valid, otherwise an exception is raised.
    :rtype: str | None
    """
    if bbox_str is None:
        return None
    if re.match(
        ",".join([parseable_float_regex for _ in range(4)]), bbox_str
    ) or re.match(",".join([parseable_float_regex for _ in range(6)]), bbox_str):
        return bbox_str
    raise ValueError("invalid bbox content")
