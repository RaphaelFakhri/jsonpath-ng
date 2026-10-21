Fixed
-----

*   Fix ``!=`` filter comparisons with literals.

    This includes fixing comparisons between string and integer values,
    as well as fixing comparisons when the target path doesn't exist.

    For example, ``parse("$[?@.a != 1]").find([{"b": 1}])`` finds ``{"b": 1}``.
    Previously, ``{"b": 1}`` was excluded because it didn't have an ``"a"`` field.

    For example, ``parse("$[?@.a != 1]").find([{"a": "x"}])`` finds ``{"a": "x"}``.
    Previously, ``{"a": "x"}`` was excluded.

    This change aligns with RFC 9535, section 2.3.5.2.2.

*   Fix a ``TypeError`` that occurs when a filter orders values of different types.

    For example, ``parse("$[?@.a < 1]").find([{"a": None}])`` now finds nothing
    instead of raising a ``TypeError``.

*   Stop speculatively coercing strings to integers in filter comparisons.

    For example, ``parse("$[?@.a == 1]").find([{"a": " +0_1"}])`` now finds nothing.
    Previously, the string ``" +0_1"`` was converted to an integer before comparing
    and would incorrectly match.

    Note that this also means that simpler numeric strings will no longer match.
    For example, ``parse("$[?@.a == 1]").find([{"a": "1"}])`` now finds nothing.
