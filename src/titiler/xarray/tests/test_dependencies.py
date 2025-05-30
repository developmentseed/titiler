"""test dependencies."""

from typing import Annotated

from fastapi import Depends, FastAPI, Path
from starlette.testclient import TestClient

from titiler.xarray import dependencies


def test_xarray_tile():
    """Create App."""
    app = FastAPI()

    @app.get("/tiles/{z}/{x}/{y}")
    def tiles(
        z: Annotated[
            int,
            Path(
                description="Identifier (Z) selecting one of the scales defined in the TileMatrixSet and representing the scaleDenominator the tile.",
            ),
        ],
        x: Annotated[
            int,
            Path(
                description="Column (X) index of the tile on the selected TileMatrix. It cannot exceed the MatrixHeight-1 for the selected TileMatrix.",
            ),
        ],
        y: Annotated[
            int,
            Path(
                description="Row (Y) index of the tile on the selected TileMatrix. It cannot exceed the MatrixWidth-1 for the selected TileMatrix.",
            ),
        ],
        params=Depends(dependencies.CompatXarrayParams),
    ):
        """return params."""
        return params.as_dict()

    with TestClient(app) as client:
        response = client.get("/tiles/1/2/3")
        params = response.json()
        assert params == {}

        response = client.get("/tiles/1/2/3", params={"variable": "yo"})
        params = response.json()
        assert params == {"variable": "yo"}

        response = client.get("/tiles/1/2/3", params={"sel": "yo=yo"})
        params = response.json()
        assert params == {"sel": ["yo=yo"]}

        response = client.get("/tiles/1/2/3", params={"sel": "yo=1.0"})
        params = response.json()
        assert params == {"sel": ["yo=1.0"]}

        response = client.get("/tiles/1/2/3", params={"sel": ["yo=yo", "ye=ye"]})
        params = response.json()
        assert params == {"sel": ["yo=yo", "ye=ye"]}

        response = client.get("/tiles/1/2/3?sel=yo=yo&sel=ye=ye")
        params = response.json()
        assert params == {"sel": ["yo=yo", "ye=ye"]}

        response = client.get("/tiles/1/2/3", params={"sel": "yo"})
        assert response.status_code == 422

        response = client.get("/tiles/1/2/3", params={"sel": "=yo"})
        assert response.status_code == 422

        response = client.get("/tiles/1/2/3", params={"sel": "yo="})
        assert response.status_code == 422

        response = client.get("/tiles/1/2/3", params={"sel_method": "nearest"})
        params = response.json()
        assert params == {"method": "nearest"}
