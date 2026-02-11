"""Test route dependencies."""

import httpx
from fastapi import Depends, FastAPI, HTTPException, security, status
from starlette.testclient import TestClient

from titiler.core.routing import add_route_dependencies


def test_register_deps():
    """Test add_route_dependencies."""

    http_basic = security.HTTPBasic()

    def must_be_bob(credentials: security.HTTPBasicCredentials = Depends(http_basic)):
        if credentials.username == "bob":
            return True
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You're not Bob",
            headers={"WWW-Authenticate": "Basic"},
        )

    app = FastAPI()

    @app.get("/one")
    def one():
        """one."""
        return "one"

    @app.get("/two")
    def two():
        """two."""
        return "two"

    auth_bob = httpx.BasicAuth(username="bob", password="ILoveSponge")
    auth_notbob = httpx.BasicAuth(username="notbob", password="IHateSponge")

    add_route_dependencies(
        app.routes,
        scopes=[
            {"path": "/one", "method": "GET"},
        ],
        dependencies=[Depends(must_be_bob)],
    )

    client = TestClient(app)

    response = client.get("/one", auth=auth_bob)
    assert response.status_code == 200

    response = client.get("/one", auth=auth_notbob)
    assert response.status_code == 401

    response = client.get("/two", auth=auth_bob)
    assert response.status_code == 200

    response = client.get("/two", auth=auth_notbob)
    assert response.status_code == 200
