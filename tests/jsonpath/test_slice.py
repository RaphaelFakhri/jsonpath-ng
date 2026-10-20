import pytest

import jsonpath_ng
import jsonpath_ng.ext

parsers = pytest.mark.parametrize(
    "parse",
    (jsonpath_ng.parse, jsonpath_ng.ext.parse),
    ids=lambda function: function.__module__,
)


@pytest.mark.parametrize(
    "data, expected_start, expected_end, expected_step",
    (
        # Special case
        pytest.param("[*]", None, None, None, id="wildcard"),
        # Individual elements
        pytest.param("[0:]", 0, None, None, id="start-false-y"),
        pytest.param("[1:]", 1, None, None, id="start-1"),
        pytest.param("[:0]", None, 0, None, id="end-false-y"),
        pytest.param("[:1]", None, 1, None, id="end-1"),
        pytest.param("[::0]", None, None, 0, id="step-nonsense"),
        pytest.param("[::1]", None, None, 1, id="step-default"),
        pytest.param("[::2]", None, None, 2, id="step-2"),
        # Paired elements
        pytest.param("[1:2]", 1, 2, None, id="start-and-end"),
        pytest.param("[:1:2]", None, 1, 2, id="end-and-step"),
        pytest.param("[1::2]", 1, None, 2, id="start-and-step"),
        # All elements
        pytest.param("[1:2:3]", 1, 2, 3, id="all-elements"),
    ),
)
@parsers
def test_slice(parse, data, expected_start, expected_end, expected_step):
    instance = parse(data)

    assert isinstance(instance, jsonpath_ng.Slice)
    assert instance.start == expected_start
    assert instance.end == expected_end
    assert instance.step == expected_step

    assert str(instance) == data


@pytest.mark.parametrize("data", (5, 1.5, True, None, "text"))
@parsers
def test_find_selects_nothing_from_scalars(parse, data):
    assert parse("$[*]").find(data) == []
    assert parse("$[0:2]").find(data) == []


@parsers
def test_find_wildcard_selects_object_member_values(parse):
    matches = parse("$.o[*]").find({"o": {"x": 1, "y": 2}})

    assert [match.value for match in matches] == [1, 2]
    assert [str(match.full_path) for match in matches] == ["o.x", "o.y"]


@parsers
def test_find_slice_with_parameters_selects_nothing_from_objects(parse):
    assert parse("$.o[0:2]").find({"o": {"x": 1, "y": 2}}) == []


@parsers
def test_update_wildcard_sets_object_member_values(parse):
    data = {"o": {"x": 1, "y": 2}, "l": [1, 2], "s": "text"}

    assert parse("$.o[*]").update(data, 0) == {
        "o": {"x": 0, "y": 0},
        "l": [1, 2],
        "s": "text",
    }


@parsers
def test_update_does_not_change_scalars(parse):
    data = {"n": 5, "s": "text"}

    assert parse("$.n[*]").update(data, 0) == {"n": 5, "s": "text"}
    assert parse("$.s[0:2]").update(data, 0) == {"n": 5, "s": "text"}


@parsers
def test_filter_wildcard_removes_object_members(parse):
    data = {"o": {"x": 1, "y": 2}}

    assert parse("$.o[*]").filter(lambda value: value == 1, data) == {"o": {"y": 2}}


@pytest.mark.parametrize(
    "query", ("$[::0]", "$[1:3:0]", "$[:2:0]", "$[1::0]", "$[-1:-3:0]")
)
@parsers
def test_find_step_zero_selects_nothing(parse, query):
    # RFC 9535 section 2.3.4.2.2: "When step = 0, no elements are selected".
    assert parse(query).find([1, 2, 3, 4]) == []


@parsers
def test_find_step_zero_selects_nothing_from_empty_array(parse):
    assert parse("$[::0]").find([]) == []


def test_find_step_zero_selects_nothing_from_tuples():
    assert jsonpath_ng.Slice(step=0).find((1, 2, 3)) == []


@parsers
def test_update_step_zero_changes_nothing(parse):
    assert parse("$[::0]").update([1, 2, 3], 9) == [1, 2, 3]


@parsers
def test_filter_step_zero_removes_nothing(parse):
    assert parse("$[::0]").filter(lambda value: True, [1, 2, 3]) == [1, 2, 3]


@parsers
def test_find_step_zero_is_not_an_error_after_a_child(parse):
    data = {"a": [1, 2, 3]}

    assert parse("$.a[::0]").find(data) == []
    assert [match.value for match in parse("$.a[::1]").find(data)] == [1, 2, 3]


@pytest.mark.parametrize(
    "query, expected",
    (
        pytest.param("$[::]", [1, 2, 3, 4], id="step-omitted-with-colons"),
        pytest.param("$[::1]", [1, 2, 3, 4], id="step-1"),
        pytest.param("$[::2]", [1, 3], id="step-2"),
        pytest.param("$[::-1]", [4, 3, 2, 1], id="step-negative-1"),
    ),
)
@parsers
def test_find_step_defaults_to_one(parse, query, expected):
    # RFC 9535 section 2.3.4.1: "The default value for step is 1."
    # An omitted step must not be confused with an explicit step of 0.
    assert [match.value for match in parse(query).find([1, 2, 3, 4])] == expected
