if not exist "%PREFIX%\Menu" mkdir "%PREFIX%\Menu"
copy "%RECIPE_DIR%\pysmith-menu-windows.json" "%PREFIX%\Menu"
copy "%RECIPE_DIR%\app.ico" "%PREFIX%\Menu"

copy "%RECIPE_DIR%\pysmith-app.py" "%SCRIPTS%"

"%PYTHON%" setup.py install --single-version-externally-managed --record=record.txt
if errorlevel 1 exit 1