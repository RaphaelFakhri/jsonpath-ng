Fixed
-----

*   Resolve ``$`` to the root node inside a filter. (#66)

    Previously, ``$`` was incorrectly treated as an alias of ``@``.
    Use ``@`` to refer to the element being tested.

    This change improves RFC 9535 compliance.
