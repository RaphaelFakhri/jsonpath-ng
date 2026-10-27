Fixed
-----

*   Fix filter ``update()`` ignoring objects.
    For example, ``$[?@ > 1]`` now updates the matching values of a dict,
    as ``find()`` and ``filter()`` already select them.
