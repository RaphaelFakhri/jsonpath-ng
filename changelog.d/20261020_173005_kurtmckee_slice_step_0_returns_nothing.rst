Fixed
-----

*   Return ``[]`` when a slice's step size is ``0``.

    For example, ``parse("$[::0]").find([1,2,3])`` now returns ``[]``.

    This aligns with RFC 9535, section 2.3.4.2.2.
