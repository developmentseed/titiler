
**Goal**: Add a custom colormap dependency to allow user pass linear `colormap` definition.

```python
# https://colorbrewer2.org/#type=sequential&scheme=BuGn&n=3
cmap = urlencode(
    {
        "colormap": json.dumps(
            {
                "0": "#e5f5f9",
                "10": "#99d8c9",
                "255": "#2ca25f",
            }
        )
    }
)
response = requests.get(
    f"http://127.0.0.1:8000/cog/tiles/WebMercatorQuad/8/53/50.png?url=https://myurl.com/cog.tif&bidx=1&rescale=0,10000&{cmap}"
)
```


**requirements**: titiler.core matplotlib


1 - Create a custom `ColorMapParams` dependency

```python
"""dependencies.

app/dependencies.py

"""

import json

from typing import Dict, Optional, Literal
from typing_extensions import Annotated

import numpy
import matplotlib
from rio_tiler.colormap import parse_color
from rio_tiler.colormap import cmap as default_cmap
from fastapi import HTTPException, Query


def ColorMapParams(
    colormap_name: Annotated[  # type: ignore
        Literal[tuple(default_cmap.list())],
        Query(description="Colormap name"),
    ] = None,
    colormap: Annotated[
        str,
        Query(description="JSON encoded custom Colormap"),
    ] = None,
    colormap_type: Annotated[
        Literal["explicit", "linear"],
        Query(description="User input colormap type."),
    ] = "explicit",
) -> Optional[Dict]:
    """Colormap Dependency."""
    if colormap_name:
        return default_cmap.get(colormap_name)

    if colormap:
        try:
            cm = json.loads(
                colormap,
                object_hook=lambda x: {int(k): parse_color(v) for k, v in x.items()},
            )
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400, detail="Could not parse the colormap value."
            )

        if colormap_type == "linear":
            # input colormap has to start from 0 to 255 ?
            cm = matplotlib.colors.LinearSegmentedColormap.from_list(
                'custom',
                [
                    (k / 255, matplotlib.colors.to_hex([v / 255 for v in rgba]))
                    for (k, rgba) in cm.items()
                ],
                256,
            )
            x = numpy.linspace(0, 1, 256)
            cmap_vals = cm(x)[:, :]
            cmap_uint8 = (cmap_vals * 255).astype('uint8')
            cm = {idx: value.tolist() for idx, value in enumerate(cmap_uint8)}

        return cm

    return None
```

2 - Create app and register our custom endpoints

```python
"""app.

app/main.py

"""

from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.factory import TilerFactory

from fastapi import FastAPI

from .dependencies import ColorMapParams

app = FastAPI(title="My simple app with custom TMS")

cog = TilerFactory(colormap_dependency=ColorMapParams)
app.include_router(cog.router, tags=["Cloud Optimized GeoTIFF"])
add_exception_handlers(app, DEFAULT_STATUS_CODES)
```
