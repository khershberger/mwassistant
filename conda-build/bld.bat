if not exist "%PREFIX%\Menu" mkdir "%PREFIX%\Menu"
copy "%RECIPE_DIR%\mwassistant-menu-windows.json" "%PREFIX%\Menu"
copy "%RECIPE_DIR%\mwassistant.ico" "%PREFIX%\Menu"

copy "%RECIPE_DIR%\mwassist-app.py" "%SCRIPTS%"

"%PYTHON%" setup.py install --single-version-externally-managed --record=record.txt
if errorlevel 1 exit 1