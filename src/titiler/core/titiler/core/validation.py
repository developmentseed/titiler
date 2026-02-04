"""Dependency validations."""

import re


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
