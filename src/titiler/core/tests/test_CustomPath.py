"""Test TiTiler Custom Path Params."""

import os
import re

from fastapi import FastAPI, HTTPException, Query
from starlette.testclient import TestClient
from typing_extensions import Annotated

from titiler.core.factory import TilerFactory

from .conftest import DATA_DIR


def CustomPathParams(
    name: Annotated[
        str,
        Query(
            alias="file",
            description="Give me a url.",
        ),
    ],
) -> str:
    """Custom path Dependency."""
    if not re.match(".+tif$", name):
        raise HTTPException(
            status_code=400,
            detail="Nope, this is not a valid File - Please Try Again",
        )

    if not os.path.exists(f"{DATA_DIR}/{name}"):
        raise HTTPException(
            status_code=404,
            detail="The File doesn't exists - Please Try Again",
        )

    return f"{DATA_DIR}/{name}"


def test_CustomPath():
    """Test Custom Render Params dependency."""
    app = FastAPI()

    cog = TilerFactory(path_dependency=CustomPathParams)
    app.include_router(cog.router)
    client = TestClient(app)

    response = client.get("/preview.png?file=cog.tif&rescale=0,10000")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    response = client.get("/preview.png?file=somethingelse.jpeg")
    assert "valid File" in response.text
    assert response.status_code == 400

    response = client.get("/preview.png?file=somethingelse.tif&rescale=0,10000")
    assert "exists" in response.text
    assert response.status_code == 404
