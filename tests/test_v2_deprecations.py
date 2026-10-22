import importlib
import re

import pytest

import jsonpath_ng
import jsonpath_ng.ext
import jsonpath_ng.ext.parser as parser
import jsonpath_ng.jsonpath
from jsonpath_ng.ext.filter import Filter
from jsonpath_ng.jsonpath import Child
from jsonpath_ng.jsonpath import Root
from tests.helpers import assert_value_equality


def test_extented_jsonpath_parser_access():
    match = "ExtentedJsonPathParser is a deprecated name"
    with pytest.warns(DeprecationWarning, match=match):
        assert parser.ExtentedJsonPathParser is parser.ExtendedJsonPathParser


def test_version_attribute_is_deprecated():
    match = "The `__version__` attribute is deprecated"
    with pytest.warns(DeprecationWarning, match=match):
        assert jsonpath_ng.__version__[0] == "1"


@pytest.mark.parametrize(
    "datum, expected_values",
    [
        pytest.param([1, 2], [1, 2], id="list"),
        pytest.param({"a": 1, "b": 2}, [1, 2], id="dict"),
        pytest.param(2, [], id="int"),
        pytest.param(None, [], id="null"),
    ],
)
def test_filter_without_expressions_is_deprecated(datum, expected_values):
    match = "Creating a Filter with no expressions is deprecated."
    with pytest.warns(DeprecationWarning, match=match):
        selector = Filter([])

    results = Child(Root(), selector).find(datum)
    assert_value_equality(results, expected_values)


PARSERS = pytest.mark.parametrize(
    "parse",
    [
        pytest.param(jsonpath_ng.parse, id="core"),
        pytest.param(jsonpath_ng.ext.parse, id="ext"),
    ],
)
PIPE_MESSAGE = r"The `\|` \(union\) operator is deprecated"
PATH_AMPERSAND_MESSAGE = r"The `&` \(intersection\) operator is deprecated"
FILTER_AMPERSAND_MESSAGE = r"The `&` operator in filters is deprecated"


@PARSERS
def test_pipe_operator_is_deprecated(parse):
    with pytest.warns(DeprecationWarning, match=PIPE_MESSAGE) as record:
        parse("a | b")

    assert len(record) == 1


@PARSERS
def test_pipe_operator_warns_once_per_operator(parse):
    with pytest.warns(DeprecationWarning, match=PIPE_MESSAGE) as record:
        parse("a | b | c")

    assert len(record) == 2


@PARSERS
def test_path_ampersand_operator_is_deprecated(parse):
    with pytest.warns(DeprecationWarning, match=PATH_AMPERSAND_MESSAGE) as record:
        parse("a & b")

    assert len(record) == 1


@pytest.mark.parametrize(
    "query",
    [
        pytest.param("$[?@.a == 1 & @.b == 1]", id="no-parentheses"),
        pytest.param("$[?(@.a == 1) & (@.b == 1)]", id="parentheses"),
    ],
)
def test_filter_ampersand_operator_is_deprecated(query):
    with pytest.warns(DeprecationWarning, match=FILTER_AMPERSAND_MESSAGE) as record:
        jsonpath_ng.ext.parse(query)

    assert len(record) == 1


def test_filter_ampersand_operator_still_works():
    with pytest.warns(DeprecationWarning, match=FILTER_AMPERSAND_MESSAGE):
        query = jsonpath_ng.ext.parse("$[?@.a == 1 & @.b == 1]")

    results = query.find([{"a": 1, "b": 1}, {"a": 1, "b": 2}])
    assert_value_equality(results, [{"a": 1, "b": 1}])


def test_pipe_operator_still_works():
    with pytest.warns(DeprecationWarning, match=PIPE_MESSAGE):
        query = jsonpath_ng.parse("a | b")

    assert_value_equality(query.find({"a": 1, "b": 2}), [1, 2])


def test_path_ampersand_operator_creates_an_intersect():
    with pytest.warns(DeprecationWarning, match=PATH_AMPERSAND_MESSAGE):
        query = jsonpath_ng.parse("a & b")

    assert type(query) is jsonpath_ng.jsonpath._Intersect


def test_parsing_a_pipe_creates_a_union():
    with pytest.warns(DeprecationWarning, match=PIPE_MESSAGE):
        query = jsonpath_ng.parse("a | b")

    assert type(query) is jsonpath_ng.jsonpath._Union


@pytest.mark.parametrize("name", ["Union", "Intersect"])
@pytest.mark.parametrize("module", ["jsonpath_ng", "jsonpath_ng.jsonpath"])
def test_union_and_intersect_access_is_deprecated(module, name):
    module = importlib.import_module(module)
    match = re.escape(f"`{name}` is deprecated")

    with pytest.warns(DeprecationWarning, match=match):
        cls = getattr(module, name)

    assert cls is getattr(jsonpath_ng.jsonpath, f"_{name}")


@pytest.mark.parametrize("name", ["Union", "Intersect"])
def test_union_and_intersect_import_is_deprecated(name):
    with pytest.warns(DeprecationWarning, match=rf"`{name}` is deprecated"):
        namespace = {}
        exec(f"from jsonpath_ng.jsonpath import {name}", namespace)

    assert namespace[name] is getattr(jsonpath_ng.jsonpath, f"_{name}")


@pytest.mark.parametrize("name", ["Union", "Intersect"])
def test_star_import_does_not_export_union_or_intersect(name):
    namespace = {}
    exec("from jsonpath_ng import *", namespace)

    assert name not in namespace


@pytest.mark.parametrize("module", [jsonpath_ng, jsonpath_ng.jsonpath])
def test_unknown_attributes_still_raise_attribute_error(module):
    with pytest.raises(AttributeError, match="NoSuchName"):
        module.NoSuchName
