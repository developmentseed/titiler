!!! important
    This has been deprecated. You can now pass `environment_dependency=lambda: {"GDAL_DISABLE_READDIR_ON_OPEN":"FALSE"}` to the Tiler Factory. This will be passed to a `rasterio.Env()` context manager on top of all gdal related blocks.

    ```python
    from titiler.core.factory import TilerFactory
    cog = TilerFactory(
        reader=COGReader,
        router_prefix="cog",
        environment_dependency=lambda: {"GDAL_DISABLE_READDIR_ON_OPEN":"FALSE"},
    )
    ```

Sometimes, specifically when using GDAL, it can be useful to have environment variables set for certain endpoints
(e.g. when using Landsat data on AWS you need `GDAL_DISABLE_READDIR_ON_OPEN=FALSE` but you don't want this environment variable set for other endpoints). To be able to do this
we created a *custom* APIRoute class which wraps classic fastapi APIRoute with a `rasterio.Env()` block: https://github.com/developmentseed/titiler/blob/8a7127ca56631c2c327713d99e80285048c3aa6c/titiler/custom/routing.py#L13-L41

Example:
    ```python
    from fastapi import FastAPI, APIRouter
    from rasterio._env import get_gdal_config
    from titiler.core.routing import apiroute_factory
    from titiler.core.factory import TilerFactory

    app = FastAPI()
    route_class = apiroute_factory({"GDAL_DISABLE_READDIR_ON_OPEN": "FALSE"})
    router = APIRouter(route_class=route_class)

    tiler = TilerFactory(router=router)

    @router.get("/simple")
    def simple():
        """should return FALSE."""
        res = get_gdal_config("GDAL_DISABLE_READDIR_ON_OPEN")
        return {"env": res}

    app.include_router(router)
    ```

!!! important
    This has only be tested for python 3.6 and 3.7.
