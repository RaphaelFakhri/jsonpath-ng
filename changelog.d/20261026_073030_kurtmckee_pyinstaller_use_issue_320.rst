Fixed
-----

*   Fix parsing in executables created by PyInstaller. (#320)

    Since v1.10.0, PLY tables have been pre-generated to improve performance.
    However, PLY imports pre-generated modules via dynamic string lookups,
    while PyInstaller finds modules to bundle based on ``import`` statements.
    This made the PLY tables invisible to PyInstaller when freezing an app,
    and resulted in ``ModuleNotFoundError`` runtime failures when the app ran.

    The pre-generated tables are now explicitly imported.
