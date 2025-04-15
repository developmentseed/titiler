"""Test utils."""

import pytest

from titiler.core.dependencies import BidxParams
from titiler.core.resources.enums import MediaType
from titiler.core.utils import (
    accept_media_type,
    deserialize_query_params,
    get_dependency_query_params,
)


def test_get_dependency_params():
    """Test dependency filtering from query params."""

    # invalid
    values, err = get_dependency_query_params(
        dependency=BidxParams, params={"bidx": ["invalid type"]}
    )
    assert values == {}
    assert err
    assert err == [
        {
            "input": "invalid type",
            "loc": (
                "query",
                "bidx",
                0,
            ),
            "msg": "Input should be a valid integer, unable to parse string as an integer",
            "type": "int_parsing",
        },
    ]

    # not in dep
    values, err = get_dependency_query_params(
        dependency=BidxParams, params={"not_in_dep": "no error, no value"}
    )
    assert values == {"indexes": None}
    assert not err

    # valid
    values, err = get_dependency_query_params(
        dependency=BidxParams, params={"bidx": [1, 2, 3]}
    )
    assert values == {"indexes": [1, 2, 3]}
    assert not err

    # valid and not in dep
    values, err = get_dependency_query_params(
        dependency=BidxParams,
        params={"bidx": [1, 2, 3], "other param": "to be filtered out"},
    )
    assert values == {"indexes": [1, 2, 3]}
    assert not err


def test_deserialize_query_params():
    """Test deserialize_query_params."""
    # invalid
    res, err = deserialize_query_params(
        dependency=BidxParams, params={"bidx": ["invalid type"]}
    )
    print(res)
    assert res == BidxParams(indexes=None)
    assert err

    # valid
    res, err = deserialize_query_params(
        dependency=BidxParams, params={"not_in_dep": "no error, no value", "bidx": [1]}
    )
    assert res == BidxParams(indexes=[1])
    assert not err


@pytest.mark.parametrize(
    "media,accept,expected",
    [
        ([MediaType.html], "text/html, application/json;q=0.8", MediaType.html),
        (
            [MediaType.html, MediaType.json],
            "application/json, text/html;q=0.8",
            MediaType.json,
        ),
        ([MediaType.xml], "application/json, text/html;q=0.8", None),
        ([MediaType.json], "", None),
        (
            [MediaType.json, MediaType.html],
            "application/json;q=1.0, text/html;q=0.8",
            MediaType.json,
        ),
        (
            [MediaType.json, MediaType.html],
            "application/json;q=1.0, text/html;q=1.0",
            MediaType.json,
        ),
        (
            [MediaType.html, MediaType.json],
            "application/json;q=1.0, text/html;q=1.0",
            MediaType.html,
        ),
        ([MediaType.html, MediaType.json], "*;q=1.0", MediaType.html),
        (
            [MediaType.json, MediaType.html],
            "application/json;q=aaa, text/html",
            MediaType.html,
        ),
        (
            [MediaType.json, MediaType.html],
            "application/json;q=0.0, text/html",
            MediaType.html,
        ),
    ],
)
def test_accept_media_type(media, accept, expected):
    """test MetadataOutputType dependency."""
    assert accept_media_type(accept, media) == expected
