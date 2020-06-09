"""test TileMatrixSets endpoints."""


def test_tilematrix(app):
    """test /tileMatrixSet endpoint."""
    response = app.get("/tileMatrixSets")
    assert response.status_code == 200
    body = response.json()
    assert len(body["tileMatrixSets"]) == 11  # morecantile has 10 defaults
    tms = list(filter(lambda m: m["id"] == "EPSG3413", body["tileMatrixSets"]))[0]
    assert tms["links"][0]["href"] == "http://testserver/tileMatrixSets/EPSG3413"


def test_tilematrixInfo(app):
    """test /tileMatrixSet endpoint."""
    response = app.get("/tileMatrixSets/EPSG3413")
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "TileMatrixSetType"
    assert body["identifier"] == "EPSG3413"
