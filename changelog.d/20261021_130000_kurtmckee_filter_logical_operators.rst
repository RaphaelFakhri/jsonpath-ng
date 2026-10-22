Added
-----

*   Support the RFC 9535 logical operators ``&&`` and ``||`` in filters. (#27)

    For example, ``parse("$[?@.a == 1 || @.b == 2 && @.c == 3]")``.

    Note that filters are currently only supported in the ``jsonpath_ng.ext`` module.

    ``&&`` binds more tightly than ``||``, and parentheses group expressions.
    The operators are valid only inside a filter.

Deprecated
----------

*   The ``|`` (union) operator between paths is deprecated.

    A ``DeprecationWarning`` is issued when the operator is used.
    It will be removed in version 2.0.0.

    There is no RFC 9535 equivalent.

    A now-deprecated path like ``($.a) | ($.b)`` can be replaced with code like this:

    ..  code-block:: python

        matches = parse("$.a").find(data) + parse("$.b").find(data)

    Beware that ``|`` binds tighter than ``.``.
    Unparenthesized paths like ``a.b | c.d`` are interpreted as ``a.(b | c).d``,
    so write each full path when migrating and test the paths and results for equivalency.

*   The ``&`` (intersection) operator between paths is deprecated.

    A ``DeprecationWarning`` is issued when the ``&`` (intersection) operator is used.
    It will be removed in version 2.0.0.

    There is no RFC 9535 equivalent.

*   The ``&`` (logical AND) operator in filters is deprecated.

    A ``DeprecationWarning`` is issued when the ``&`` (logical AND) operator is used.
    It will be removed in version 2.0.0.

    Its RFC 9535 equivalent is ``&&``.
    Use ``&&`` instead of ``&`` in filters.

*   The ``Union`` and ``Intersect`` classes are deprecated.

    A ``DeprecationWarning`` is issued when they are accessed.
    They will be removed in version 2.0.0.

Fixed
-----

*   Serialize filters so that they can be parsed again.

    Note that ``this`` in a filter selector is now replaced with ``@``,
    which is the RFC 9535 compliant syntax.

    Similarly, strings are single-quoted and ``&`` is replaced with ``&&``
    as is required by RFC 9535.

    For example, ``str(parse("$[?`this`.a == 1 & @.b == x]"))``
    now returns ``$[?@.a == 1 && @.b == 'x']``.

*   Quote field names that begin with ``@`` when serializing a query,
    unless the ``@`` is followed by a letter or an underscore.

    For example, ``str(jsonpath_ng.ext.parse("$['@']"))`` now returns ``$.'@'``.
    Previously it returned ``$.@``, which ``jsonpath_ng.ext`` parsed as the current node.
