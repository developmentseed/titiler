"""test TileMatrixSets endpoints."""

import morecantile

NB_DEFAULT_TMS = len(morecantile.tms.list())


def test_tilematrix(app):
    """test /tileMatrixSet endpoint."""
    response = app.get("/tileMatrixSets")
    assert response.status_code == 200
    body = response.json()
    assert (
        len(body["tileMatrixSets"]) == NB_DEFAULT_TMS + 2
    )  # morecantile defaults + 2 customs
    tms = list(filter(lambda m: m["id"] == "EPSG3413", body["tileMatrixSets"]))[0]
    assert tms["links"][0]["href"] == "http://testserver/tileMatrixSets/EPSG3413"


def test_tilematrixInfo(app):
    """test /tileMatrixSet endpoint."""
    response = app.get("/tileMatrixSets/EPSG3413")
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "TileMatrixSetType"
    assert body["identifier"] == "EPSG3413"
