# """Test TiTiler Tiler Factories."""

from rio_tiler.io import COGReader as COGReaderNoTMS
from rio_tiler_crs import COGReader as COGReaderWithTMS


def test_TilerFactory(set_env):
    """Test TilerFactory class."""
    from titiler.dependencies import (
        AssetsParams,
        DefaultDependency,
        TMSParams,
        WebMercatorTMSParams,
    )
    from titiler.endpoints import factory

    app = factory.TMSTilerFactory(reader=COGReaderWithTMS)
    assert len(app.router.routes) == 19

    assert app.tms_dependency == TMSParams
    assert app.additional_dependency == DefaultDependency
    assert not app.router_prefix

    app = factory.TilerFactory(reader=COGReaderNoTMS)
    assert app.tms_dependency == WebMercatorTMSParams

    app = factory.TilerFactory(
        reader=COGReaderNoTMS,
        additional_dependency=AssetsParams,
        router_prefix="cog",
        add_preview=False,
        add_part=False,
    )
    assert len(app.router.routes) == 16
    assert app.additional_dependency == AssetsParams
    for route in app.router.routes:
        assert route.name.startswith("cog_")


def test_MosaicTilerFactory(set_env):
    """Test MosaicTilerFactory class."""
    from titiler.dependencies import DefaultDependency, WebMercatorTMSParams
    from titiler.endpoints import factory

    app = factory.MosaicTilerFactory()
    assert len(app.router.routes) == 18
    assert app.tms_dependency == WebMercatorTMSParams

    app = factory.MosaicTilerFactory(add_create=False, add_update=False)
    assert len(app.router.routes) == 16
    assert app.additional_dependency == DefaultDependency
