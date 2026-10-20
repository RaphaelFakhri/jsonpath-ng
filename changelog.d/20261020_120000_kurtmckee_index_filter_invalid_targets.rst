Fixed
-----

*   Fix crashes and other issues with filtering by array index.

    Out-of-range indices and non-array values are now ignored,
    and queries that select several indices
    (for example, ``$[0,1]``, ``$[0,2]``, or ``$[0,-3]``)
    now remove exactly the selected elements.
