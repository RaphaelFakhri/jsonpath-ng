Deprecated
----------

*   Deprecate parsing unquoted words as comparison operands in filter selectors.

    Support for parsing unquoted strings will be removed in version 2.0.0.

    For example: ``foo`` in ``$[?@.a == foo]`` is now deprecated.
    Replace usages with a quoted string, like ``$[?@.a == 'foo']``.
