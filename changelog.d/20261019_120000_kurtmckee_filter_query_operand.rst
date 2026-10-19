Added
-----

*   Support a query on the right-hand side of a filter comparison. (#79)

    For example: ``$.items[?@.a == @.b]`` and ``$.items[?@.v == $.ref.v]``.

    The query must start with ``@`` or ``$``
    and may only contain name and index segments,
    as required by RFC 9535.
