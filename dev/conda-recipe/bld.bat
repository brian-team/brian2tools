xcopy /I /Y /e "%RECIPE_DIR%\..\..\brian2tools" "%SRC_DIR%\brian2tools\"
xcopy "%RECIPE_DIR%\..\..\setup.py" "%SRC_DIR%"
xcopy "%RECIPE_DIR%\..\..\README.rst" "%SRC_DIR%"
"%PYTHON%" "%SRC_DIR%"\setup.py install --single-version-externally-managed --record=record.txt
if errorlevel 1 exit 1