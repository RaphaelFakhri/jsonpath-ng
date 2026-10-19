#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import operator
import re
import warnings

from .. import DatumInContext
from .. import Fields
from .. import Index
from .. import JSONPath
from .. import Root

OPERATOR_MAP = {
    "!=": operator.ne,
    "==": operator.eq,
    "=": operator.eq,
    "<=": operator.le,
    "<": operator.lt,
    ">=": operator.ge,
    ">": operator.gt,
    "=~": lambda a, b: True if isinstance(a, str) and re.search(b, a) else False,
}

# RFC 9535 section 2.3.5.2.2: `a != b` is true if and only if `a == b` is false,
# and `a <= b` is true if and only if `a < b` or `a == b`.
#
# Only numbers and strings are ordered, so for JSON null and for booleans
# the ordering comparisons reduce to equality.
# Each function receives whether the two values are equal.
EQUALITY_ONLY_OPERATOR_MAP = {
    "!=": operator.not_,
    "==": bool,
    "=": bool,
    "<=": bool,
    ">=": bool,
    "<": lambda equal: False,
    ">": lambda equal: False,
}


class Filter(JSONPath):
    """The JSONQuery filter"""

    def __init__(self, expressions) -> None:
        if not expressions:
            msg = (
                "Creating a Filter with no expressions is deprecated. "
                "It will raise an exception in version 2.0.0."
            )
            warnings.warn(msg, DeprecationWarning, stacklevel=2)
        self.expressions = list(expressions)

    def _references_root(self) -> bool:
        """Identify whether the filter expressions reference the root identifier."""

        paths_to_visit: list[JSONPath] = list(self.expressions)

        while paths_to_visit:
            path = paths_to_visit.pop()
            if isinstance(path, Root):
                return True

            if isinstance(path, Filter):
                paths_to_visit.extend(path.expressions)
            elif isinstance(path, Expression):
                paths_to_visit.append(path.target)
            else:
                if (left := getattr(path, "left", None)) is not None:
                    paths_to_visit.append(left)
                if (right := getattr(path, "right", None)) is not None:
                    paths_to_visit.append(right)

        return False

    def find(self, datum):
        datum = DatumInContext.wrap(datum)

        if isinstance(datum.value, dict):
            candidates = datum.value.items()
            make_path = Fields
        elif isinstance(datum.value, list):
            candidates = enumerate(datum.value)
            make_path = Index
        else:
            return []

        # RFC 9535 section 1.4.1: `$` is the root of the query argument,
        # so an expression that uses it must be evaluated on a candidate
        # that is linked to its parent.
        if self._references_root():
            results = []
            for key, value in candidates:
                candidate = DatumInContext(value, path=make_path(key), context=datum)
                if all(expression.find(candidate) for expression in self.expressions):
                    results.append(candidate)
            return results

        # Otherwise, avoid creating candidates that will not match.
        return [
            DatumInContext(value, path=make_path(key), context=datum)
            for key, value in candidates
            if all(expression.find(value) for expression in self.expressions)
        ]

    @staticmethod
    def _datum(data, root):
        """Wrap *data* so that `$` resolves to *root*."""

        if data is root:
            return DatumInContext(data)
        return DatumInContext(data, context=DatumInContext(root))

    def filter(self, fn, data):
        return self._filter_with_root(fn, data, data)

    def _filter_with_root(self, fn, data, root):
        # Reverse the order to ensure indices are preserved upon removal.
        for datum in reversed(self.find(self._datum(data, root))):
            datum.path.filter(fn, data)
        return data

    def update(self, data, val):
        return self._update_with_root(data, val, data)

    def _update_with_root(self, data, val, root):
        if type(data) is list:
            if self._references_root():
                # Evaluate `$` against the root, as `find()` does.
                parent = self._datum(data, root)
                for index, item in enumerate(data):
                    candidate = DatumInContext(item, path=Index(index), context=parent)
                    if all(
                        expression.find(candidate) for expression in self.expressions
                    ):
                        self._set(data, index, val)
            else:
                for index, item in enumerate(data):
                    if all(expression.find(item) for expression in self.expressions):
                        self._set(data, index, val)
        return data

    @staticmethod
    def _set(data, index, val):
        if callable(val):
            val(data[index], data, index)
        else:
            data[index] = val

    def __repr__(self):
        return f"{self.__class__.__name__}({self.expressions!r})"

    def __str__(self):
        return "[?%s]" % self.expressions

    def __eq__(self, other):
        return isinstance(other, Filter) and self.expressions == other.expressions


class Expression(JSONPath):
    """The JSONQuery expression"""

    def __init__(self, target, op, value) -> None:
        self.target = target
        self.op = op
        self.value = value

    def find(self, datum):
        wrapped_datum = DatumInContext.wrap(datum)
        found = self.target.find(wrapped_datum)

        if self.op == "!":
            return [] if found else [wrapped_datum]

        # A comparison with the literal `null` has `None` as its value, which is
        # otherwise only the case for the existence test and negation handled above.
        null_comparison = self.op is not None and self.value is None
        if not found:
            # RFC 9535 section 2.3.5.2.2: a missing value is not equal to `null`.
            return [wrapped_datum] if null_comparison and self.op == "!=" else []
        if self.op is None:
            return found

        result = []
        for data in found:
            value = data.value
            if null_comparison:
                if EQUALITY_ONLY_OPERATOR_MAP[self.op](value is None):
                    result.append(data)
                continue
            if self.op != "=~" and (
                isinstance(value, bool) or isinstance(self.value, bool)
            ):
                # A boolean is never equal to a number according to RFC 9535.
                # However, in Python, bool is a subclass of int and is comparable
                # via equality (`False == 0`, `True == 1`).
                # Therefore, an identity comparison (`is`) is used,
                # which relies on the fact that bools in Python are singletons.
                if EQUALITY_ONLY_OPERATOR_MAP[self.op](value is self.value):
                    result.append(data)
                continue
            if type(self.value) is int and isinstance(value, str):
                try:
                    value = int(value)
                except ValueError:
                    continue

            if OPERATOR_MAP[self.op](value, self.value):
                result.append(data)

        return result

    def __eq__(self, other):
        return (
            isinstance(other, Expression)
            and self.target == other.target
            and self.op == other.op
            and self.value == other.value
        )

    def __repr__(self):
        if self.op is None:
            return f"{self.__class__.__name__}({self.target!r})"
        else:
            return "{}({!r} {} {!r})".format(
                self.__class__.__name__, self.target, self.op, self.value
            )

    def __str__(self):
        if self.op is None:
            return "%s" % self.target
        else:
            value = "null" if self.value is None else self.value
            return f"{self.target} {self.op} {value}"
