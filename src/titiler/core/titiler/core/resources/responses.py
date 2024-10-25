"""Common response models."""

from typing import Any

import numpy
import simplejson as json
from starlette import responses


class XMLResponse(responses.Response):
    """XML Response"""

    media_type = "application/xml"


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON Encoder."""

    def default(self, obj):
        """Catch numpy types and convert them."""
        if isinstance(obj, (numpy.ndarray, numpy.generic)):
            return obj.tolist()
        return super().default(obj)


class JSONResponse(responses.JSONResponse):
    """Custom JSON Response."""

    def render(self, content: Any) -> bytes:
        """Render JSON.

        Same defaults as starlette.responses.JSONResponse.render but allow NaN to be replaced by null using simplejson
        """
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            ignore_nan=True,
            separators=(",", ":"),
            cls=NumpyEncoder,
        ).encode("utf-8")


class GeoJSONResponse(JSONResponse):
    """GeoJSON Response"""

    media_type = "application/geo+json"
