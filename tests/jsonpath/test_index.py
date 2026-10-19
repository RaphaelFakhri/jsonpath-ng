import copy

import pytest

import jsonpath_ng
import jsonpath_ng.ext
from jsonpath_ng.jsonpath import Index

parsers = pytest.mark.parametrize(
    "parse",
    (jsonpath_ng.parse, jsonpath_ng.ext.parse),
    ids=lambda function: function.__module__,
)


@pytest.mark.parametrize(
    "indices, expected",
    (
        ((0,), "[0]"),
        ((-1,), "[-1]"),
        ((0, 1), "[0,1]"),
        ((0, 1, 2), "[0,1,2]"),
        ((0, -1), "[0,-1]"),
    ),
)
def test_str(indices, expected):
    assert str(Index(*indices)) == expected


@pytest.mark.parametrize(
    "expression",
    (
        "[0]",
        "[0,1]",
        "[0,1,2]",
    ),
)
@parsers
def test_str_roundtrip(parse, expression):
    parsed = parse(expression)
    reserialized = str(parsed)

    assert reserialized == expression
    assert parsed == parse(reserialized)


@pytest.mark.parametrize(
    "expression, data", (("[0]", []), ("[2]", [1, 2]), ("[-3]", [1, 2]))
)
@pytest.mark.parametrize("use_callback", (False, True))
@parsers
def test_update_ignores_out_of_range_indices(parse, expression, data, use_callback):
    data = copy.deepcopy(data)
    original = data.copy()

    def callback(value, parent, index):
        pytest.fail("The callback must not run when no index matches")

    path = parse(expression)
    assert path.find(data) == []
    assert path.update(data, callback if use_callback else 99) is data
    assert data == original


@pytest.mark.parametrize("data", ({"value": 1}, "abc", None, (1, 2)))
@pytest.mark.parametrize("use_callback", (False, True))
@parsers
def test_update_ignores_non_arrays(parse, data, use_callback):
    data = copy.deepcopy(data)
    original = copy.deepcopy(data)

    def callback(value, parent, index):
        pytest.fail("The callback must not run when no mutable array matches")

    assert parse("[0]").update(data, callback if use_callback else 99) is data
    assert data == original


@pytest.mark.parametrize("mode", ("value", "callback", "values"))
@parsers
def test_update_mixed_indices_preserves_valid_selection_order(parse, mode):
    data = [1, 2, 3]
    calls = []

    def callback(value, parent, index):
        assert parent is data
        calls.append(index)
        return value * 10

    replacement = {
        "value": 99,
        "callback": callback,
        "values": ["first", "last"],
    }[mode]
    expected = {
        "value": [99, 2, 99],
        "callback": [10, 2, 30],
        "values": ["first", 2, "last"],
    }[mode]

    assert parse("[99,-99,0,-1]").update(data, replacement) is data
    assert data == expected
    assert calls == ([0, -1] if mode == "callback" else [])


@pytest.mark.parametrize("use_callback", (False, True))
@parsers
def test_update_valid_negative_boundary(parse, use_callback):
    data = [1, 2]
    replacement = (lambda value, parent, index: 99) if use_callback else 99
    assert parse("[-2]").update(data, replacement) is data
    assert data == [99, 2]


@pytest.mark.parametrize("use_callback", (False, True))
@parsers
def test_update_or_create_still_pads_arrays(parse, use_callback):
    data = [1]
    replacement = (lambda value, parent, index: 99) if use_callback else 99
    assert parse("[2]").update_or_create(data, replacement) is data
    assert data == [1, {}, 99]
