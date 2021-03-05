"""Test TiTiler Custom Path Params."""

import re

from titiler.endpoints import factory

from .conftest import DATA_DIR

from fastapi import FastAPI, HTTPException, Query

from starlette.testclient import TestClient


def CustomPathParams(url: str = Query(..., description="Give me a url.",)) -> str:
    """Custom path Dependency."""
    if not re.match("^c.+tif$", url):
        raise HTTPException(
            status_code=400, detail="Nope, this is not a valid URL - Please Try Again",
        )
    return f"{DATA_DIR}/{url}"


def test_CustomPath():
    """Test Custom Render Params dependency."""
    app = FastAPI()

    cog = factory.TilerFactory(path_dependency=CustomPathParams)
    app.include_router(cog.router)
    client = TestClient(app)

    response = client.get("/preview.png?url=cog.tif&rescale=0,10000")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    response = client.get("/preview.png?url=somethingelse.tif&rescale=0,10000")
    assert response.status_code == 400
