"""test dependencies."""

from typing import Annotated, Optional

from fastapi import Depends, FastAPI, Path
from starlette.testclient import TestClient

from titiler.core.resources.enums import MediaType
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

        response = client.get("/tiles/1/2/3", params={"drop_dim": "yo=yo"})
        params = response.json()
        assert params == {"drop_dim": ["yo=yo"]}

        response = client.get("/tiles/1/2/3", params={"drop_dim": "yo=1.0"})
        params = response.json()
        assert params == {"drop_dim": ["yo=1.0"]}

        response = client.get("/tiles/1/2/3", params={"drop_dim": ["yo=yo", "ye=ye"]})
        params = response.json()
        assert params == {"drop_dim": ["yo=yo", "ye=ye"]}

        response = client.get("/tiles/1/2/3", params={"drop_dim": "yo"})
        assert response.status_code == 422

        response = client.get("/tiles/1/2/3", params={"drop_dim": "=yo"})
        assert response.status_code == 422

        response = client.get("/tiles/1/2/3", params={"drop_dim": "yo="})
        assert response.status_code == 422


def test_xarray_mediatype_dep():
    """test MetadataOutputType dependency."""
    app = FastAPI()

    @app.get("/endpoint")
    def endpoint(
        output_type: Annotated[
            Optional[MediaType],
            Depends(dependencies.MetadataOutputType),
        ] = None,
    ):
        """return params."""
        return {"format": output_type}

    with TestClient(app) as client:
        response = client.get("/endpoint")
        params = response.json()
        assert params == {"format": None}

        response = client.get("/endpoint", params={"f": "html"})
        params = response.json()
        assert params == {"format": "text/html"}

        response = client.get("/endpoint", params={"f": "json"})
        params = response.json()
        assert params == {"format": "application/json"}

        response = client.get(
            "/endpoint", headers={"Accept": "application/json,text/html"}
        )
        params = response.json()
        assert params == {"format": "application/json"}

        # application/json is the first mediatype defined by list ["json", "html"]
        response = client.get(
            "/endpoint", headers={"Accept": "text/html,application/json"}
        )
        params = response.json()
        assert params == {"format": "application/json"}

        response = client.get(
            "/endpoint", headers={"Accept": "text/html,application/json;q=0.8"}
        )
        params = response.json()
        assert params == {"format": "text/html"}

        # application/json is the first mediatype defined by list ["json", "html"]
        response = client.get("/endpoint", headers={"Accept": "*"})
        params = response.json()
        assert params == {"format": "application/json"}
