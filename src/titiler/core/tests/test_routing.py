"""Test Custom APIRoute factory."""

from concurrent import futures

import httpx
import pytest
import rasterio
from fastapi import APIRouter, Depends, FastAPI, HTTPException, security, status
from rasterio._env import get_gdal_config
from starlette.testclient import TestClient

from titiler.core.routing import add_route_dependencies, apiroute_factory


@pytest.mark.xfail
def test_withoutCustomRoute(monkeypatch):
    """Create App."""
    monkeypatch.setenv("GDAL_DISABLE_READDIR_ON_OPEN", "something")

    app = FastAPI()
    router = APIRouter()

    def f(r):
        return get_gdal_config("GDAL_DISABLE_READDIR_ON_OPEN")

    @router.get("/simple")
    def home():
        """Works and should return FALSE."""
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="FALSE"):
            res = get_gdal_config("GDAL_DISABLE_READDIR_ON_OPEN")
        return {"env": res}

    @router.get("/asimple")
    async def home1():
        """Works and should return FALSE."""
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="FALSE"):
            res = get_gdal_config("GDAL_DISABLE_READDIR_ON_OPEN")
        return {"env": res}

    @router.get("/future")
    def home2():
        """Doesn't work and should return the value from env."""
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="FALSE"):
            with futures.ThreadPoolExecutor() as executor:
                res = list(executor.map(f, range(1)))[0]
        return {"env": res}

    @router.get("/afuture")
    async def home3():
        """Works and should return FALSE."""
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="FALSE"):
            with futures.ThreadPoolExecutor() as executor:
                res = list(executor.map(f, range(1)))[0]
        return {"env": res}

    app.include_router(router)
    client = TestClient(app)

    response = client.get("/simple")
    assert response.json()["env"] == "FALSE"

    response = client.get("/asimple")
    assert response.json()["env"] == "FALSE"

    # confirm the multi threads case doesn't work
    response = client.get("/future")
    assert not response.json()["env"] == "FALSE"

    response = client.get("/afuture")
    assert response.json()["env"] == "FALSE"


@pytest.mark.xfail
def test_withCustomRoute(monkeypatch):
    """Create App."""
    monkeypatch.setenv("GDAL_DISABLE_READDIR_ON_OPEN", "something")

    app = FastAPI()

    env = {"GDAL_DISABLE_READDIR_ON_OPEN": "FALSE"}
    with pytest.warns(DeprecationWarning):
        route_class = apiroute_factory(env)
    router = APIRouter(route_class=route_class)

    def f(r):
        return get_gdal_config("GDAL_DISABLE_READDIR_ON_OPEN")

    @router.get("/simple")
    def home():
        """Works and should return FALSE."""
        res = get_gdal_config("GDAL_DISABLE_READDIR_ON_OPEN")
        return {"env": res}

    @router.get("/asimple")
    async def home1():
        """Works and should return FALSE."""
        res = get_gdal_config("GDAL_DISABLE_READDIR_ON_OPEN")
        return {"env": res}

    @router.get("/future")
    def home2():
        """Doesn't work and should return the value from env."""
        with futures.ThreadPoolExecutor() as executor:
            res = list(executor.map(f, range(1)))[0]
        return {"env": res}

    @router.get("/afuture")
    async def home3():
        """Works and should return FALSE."""
        with futures.ThreadPoolExecutor() as executor:
            res = list(executor.map(f, range(1)))[0]
        return {"env": res}

    app.include_router(router)
    client = TestClient(app)

    response = client.get("/simple")
    assert response.json()["env"] == "FALSE"

    response = client.get("/asimple")
    assert response.json()["env"] == "FALSE"

    # confirm the Custom APIRoute class fix
    response = client.get("/future")
    assert response.json()["env"] == "FALSE"

    response = client.get("/afuture")
    assert response.json()["env"] == "FALSE"


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
