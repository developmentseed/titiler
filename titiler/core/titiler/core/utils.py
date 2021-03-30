"""TiTiler utility functions."""

import time
from typing import Dict, Optional, Tuple

from geojson_pydantic.features import Feature


# This code is copied from marblecutter
#  https://github.com/mojodna/marblecutter/blob/master/marblecutter/stats.py
# License:
# Original work Copyright 2016 Stamen Design
# Modified work Copyright 2016-2017 Seth Fitzsimmons
# Modified work Copyright 2016 American Red Cross
# Modified work Copyright 2016-2017 Humanitarian OpenStreetMap Team
# Modified work Copyright 2017 Mapzen
class Timer(object):
    """Time a code block."""

    def __enter__(self):
        """Starts timer."""
        self.start = time.time()
        return self

    def __exit__(self, ty, val, tb):
        """Stops timer."""
        self.end = time.time()
        self.elapsed = self.end - self.start

    @property
    def from_start(self):
        """Return time elapsed from start."""
        return time.time() - self.start


def bbox_to_feature(
    bbox: Tuple[float, float, float, float], properties: Optional[Dict] = None,
) -> Feature:
    """Create a GeoJSON feature polygon from a bounding box."""
    return Feature(
        **{
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [bbox[0], bbox[3]],
                        [bbox[0], bbox[1]],
                        [bbox[2], bbox[1]],
                        [bbox[2], bbox[3]],
                        [bbox[0], bbox[3]],
                    ]
                ],
            },
            "properties": {} or properties,
            "type": "Feature",
        }
    )
