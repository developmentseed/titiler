"""Test TiTiler Custom Colormap Params."""

from io import BytesIO

import numpy
from fastapi import FastAPI
from rio_tiler.colormap import ColorMaps
from starlette.testclient import TestClient

from titiler.core.dependencies import create_colormap_dependency
from titiler.core.factory import TilerFactory

from .conftest import DATA_DIR

cmap_values = {
    "cmap1": {6: (4, 5, 6, 255)},
}
cmap = ColorMaps(data=cmap_values)

ColorMapParams = create_colormap_dependency(cmap)


def test_CustomCmap():
    """Test Custom Render Params dependency."""
    app = FastAPI()
    cog = TilerFactory(colormap_dependency=ColorMapParams)
    app.include_router(cog.router)
    client = TestClient(app)

    response = client.get(
        f"/preview.npy?url={DATA_DIR}/above_cog.tif&bidx=1&colormap_name=cmap1"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-binary"
    data = numpy.load(BytesIO(response.content))
    assert 4 in data[0]
    assert 5 in data[1]
    assert 6 in data[2]

    response = client.get(
        f"/preview.npy?url={DATA_DIR}/above_cog.tif&bidx=1&colormap_name=another_cmap"
    )
    assert response.status_code == 422
