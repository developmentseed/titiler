# """Test TiTiler Tiler Factories."""

from rio_tiler.io import COGReader


def test_TilerFactory(set_env):
    """Test TilerFactory class."""
    from titiler.dependencies import TMSParams
    from titiler.endpoints import factory

    app = factory.TilerFactory(reader=COGReader)
    assert len(app.router.routes) == 21
    assert app.tms_dependency == TMSParams

    app = factory.TilerFactory(reader=COGReader, add_preview=False, add_part=False)
    assert len(app.router.routes) == 17


def test_MosaicTilerFactory(set_env):
    """Test MosaicTilerFactory class."""
    from titiler.dependencies import WebMercatorTMSParams
    from titiler.endpoints import factory

    app = factory.MosaicTilerFactory()
    assert len(app.router.routes) == 18
    assert app.tms_dependency == WebMercatorTMSParams
