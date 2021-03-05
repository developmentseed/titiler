# """Test TiTiler Custom Colormap Params."""

from enum import Enum
from io import BytesIO
from typing import Dict, Optional

import numpy
from rio_tiler.colormap import ColorMaps

from titiler.endpoints import factory

from .conftest import DATA_DIR

from fastapi import FastAPI, Query

from starlette.testclient import TestClient

cmap_values = {
    "cmap1": {6: (4, 5, 6, 255)},
}
cmap = ColorMaps(data=cmap_values)
ColorMapNames = Enum(  # type: ignore
    "ColorMapNames", [(a, a) for a in sorted(cmap.list())]
)


def ColorMapParams(
    color_map: ColorMapNames = Query(None, description="Colormap name",)
) -> Optional[Dict]:
    """Colormap Dependency."""
    if color_map:
        return cmap.get(color_map.value)
    return None


def test_CustomCmap():
    """Test Custom Render Params dependency."""
    app = FastAPI()
    cog = factory.TilerFactory(colormap_dependency=ColorMapParams)
    app.include_router(cog.router)
    client = TestClient(app)

    response = client.get(
        f"/preview.npy?url={DATA_DIR}/above_cog.tif&bidx=1&color_map=cmap1"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-binary"
    data = numpy.load(BytesIO(response.content))
    assert 4 in data[0]
    assert 5 in data[1]
    assert 6 in data[2]

    response = client.get(
        f"/preview.npy?url={DATA_DIR}/above_cog.tif&bidx=1&color_map=another_cmap"
    )
    assert response.status_code == 422
