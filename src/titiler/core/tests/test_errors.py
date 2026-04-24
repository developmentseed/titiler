"""Test titiler.core error handlers with compression middleware."""

from fastapi import FastAPI
from rio_tiler.errors import EmptyMosaicError, NoAssetFoundError
from starlette.testclient import TestClient
from starlette_cramjam.middleware import CompressionMiddleware

from titiler.core.errors import add_exception_handlers
from titiler.mosaic.errors import MOSAIC_STATUS_CODES


def _make_app(minimum_size: int) -> TestClient:
    app = FastAPI()

    @app.get("/tile")
    def tile():
        raise EmptyMosaicError("no data")

    @app.get("/noasset")
    def noasset():
        raise NoAssetFoundError("no asset")

    add_exception_handlers(app, MOSAIC_STATUS_CODES)

    app.add_middleware(
        CompressionMiddleware,
        minimum_size=minimum_size,
        exclude_mediatype={"image/jpeg", "image/png", "image/webp", "image/jp2"},
        compression_level=6,
    )
    return TestClient(app, raise_server_exceptions=False)


def test_204_minimum_size_zero_adds_content_encoding():
    """Demonstrate why minimum_size=0 is wrong for 204 responses.

    With minimum_size=0, cramjam compresses the empty body (b"") and sets
    Content-Encoding: gzip plus Content-Length: ~20. A 204 No Content response
    MUST NOT have a body (RFC 9110 §15.3.5). When served through uvicorn/h11,
    this causes 'Too much data for declared Content-Length'.

    Regression for https://github.com/developmentseed/titiler/issues/1348.
    """
    client = _make_app(minimum_size=0)
    response = client.get("/tile", headers={"Accept-Encoding": "gzip"})
    assert response.status_code == 204
    # With minimum_size=0, cramjam wrongly sets these headers on a 204
    assert response.headers.get("content-encoding") == "gzip"
    assert int(response.headers.get("content-length", "0")) > 0


def test_204_with_accept_encoding_gzip():
    """204 No Content must not produce Content-Encoding or body when served with gzip.

    minimum_size=1 skips compression for 0-byte (empty) bodies, keeping the 204
    response well-formed for h11 / HTTP/1.1.
    """
    client = _make_app(minimum_size=1)
    response = client.get("/tile", headers={"Accept-Encoding": "gzip"})
    assert response.status_code == 204
    assert response.content == b""
    assert "content-encoding" not in response.headers


def test_204_no_asset_with_accept_encoding():
    """NoAssetFoundError -> 204 must also survive compression middleware."""
    client = _make_app(minimum_size=1)
    response = client.get("/noasset", headers={"Accept-Encoding": "gzip, br"})
    assert response.status_code == 204
    assert response.content == b""
    assert "content-encoding" not in response.headers


def test_204_without_accept_encoding_unaffected():
    """204 without Accept-Encoding header must be unaffected by this change."""
    client = _make_app(minimum_size=1)
    response = client.get("/tile")
    assert response.status_code == 204
    assert response.content == b""
