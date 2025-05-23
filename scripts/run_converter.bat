@echo off
REM Batch file to run the SAGA Species CSV to JSON Python script
REM Created on: May 23, 2025

REM Script path - ensure this is correct
SET PYTHON_SCRIPT_PATH="D:\OneDrive\Documents\GitHub\SagaIndex\scripts\saga_character_multi_converter.py"

REM Ensure Python is in your PATH or the 'py' launcher is available.
echo Running Python script: %PYTHON_SCRIPT_PATH%
echo Please wait, this may take a moment...
echo.

REM Option 1: Using the 'py' launcher (recommended if available)
py %PYTHON_SCRIPT_PATH%

REM Option 2: Calling python.exe directly
REM If the 'py' launcher doesn't work, or you need to specify a particular Python installation,
REM you can try using the full path to your python.exe.
REM Uncomment the line below and update the path to your python.exe if needed.
REM "C:\Path\To\Your\Python\Installation\python.exe" %PYTHON_SCRIPT_PATH%

echo.
echo Script execution finished.
pause