"""TiTiler utility functions."""

import time
from typing import Any, Dict, List, Optional, Tuple

import numpy
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


def data_stats(
    data: numpy.ma.array,
    categorical: bool = False,
    categories: Optional[List[float]] = None,
    percentiles: List[int] = [2, 98],
) -> List[Dict[str, Any]]:
    """Returns statistics."""
    output = []
    percentiles_names = [f"percentile_{int(p)}" for p in percentiles]
    for b in range(data.shape[0]):
        keys, counts = numpy.unique(data[b].data, return_counts=True)
        valid_percent = round(
            (1 - numpy.ma.count_masked(data[b]) / data[b].size) * 100, 2
        )

        if categorical:
            # if input categories we make sure to use the same type as the data
            out_keys = (
                numpy.array(categories).astype(keys.dtype) if categories else keys
            )
            out_dict = dict(zip(keys.tolist(), counts.tolist()))
            output.append(
                {
                    "categories": {k: out_dict.get(k, 0) for k in out_keys.tolist()},
                    "valid_percent": valid_percent,
                },
            )
        else:
            percentiles_values = numpy.percentile(data[b], percentiles).tolist()

            v = {
                "min": float(data[b].min()),
                "max": float(data[b].max()),
                "mean": float(data[b].mean()),
                "count": float(data[b].count()),
                "sum": float(data[b].sum()),
                "std": float(data[b].std()),
                "median": float(numpy.ma.median(data[b])),
            }
            v.update(dict(zip(percentiles_names, percentiles_values)))
            v["valid_percent"] = valid_percent
            output.append(v)

    return output
