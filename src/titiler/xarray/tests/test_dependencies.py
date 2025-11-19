"""test dependencies."""

from fastapi import Depends, FastAPI
from starlette.testclient import TestClient

from titiler.xarray import dependencies


def test_xarray_tile():
    """Create App."""
    app = FastAPI()

    @app.get("/")
    def endpoint(
        params=Depends(dependencies.CompatXarrayParams),
    ):
        """return params."""
        return params.as_dict()

    with TestClient(app) as client:
        response = client.get("/")
        params = response.json()
        assert params == {}

        response = client.get("/", params={"variable": "yo"})
        params = response.json()
        assert params == {"variable": "yo"}

        response = client.get("/", params={"sel": "yo=yo"})
        params = response.json()
        assert params == {"sel": ["yo=yo"]}

        response = client.get("/", params={"sel": "yo=1.0"})
        params = response.json()
        assert params == {"sel": ["yo=1.0"]}

        response = client.get("/", params={"sel": ["yo=yo", "ye=ye"]})
        params = response.json()
        assert params == {"sel": ["yo=yo", "ye=ye"]}

        response = client.get("/?sel=yo=yo&sel=ye=ye")
        params = response.json()
        assert params == {"sel": ["yo=yo", "ye=ye"]}

        response = client.get("/", params={"sel": "yo"})
        assert response.status_code == 422

        response = client.get("/", params={"sel": "=yo"})
        assert response.status_code == 422

        response = client.get("/", params={"sel": "yo="})
        assert response.status_code == 422

        response = client.get("/", params={"sel": "time=near::2023-01-01"})
        assert response.status_code == 422

        response = client.get("/", params={"sel": ["yo=nearest::yo", "ye=ye"]})
        params = response.json()
        assert params == {"sel": ["yo=nearest::yo", "ye=ye"]}
