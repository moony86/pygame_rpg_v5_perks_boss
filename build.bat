@echo off
cd /d "%~dp0"

rem Frozen builds disable developer tools automatically; tests use source defaults.
set BLUECUBE_DEV_TOOLS=

if not exist ".build-venv\Scripts\python.exe" (
    py -3.12 -m venv .build-venv
    if errorlevel 1 goto failed
)
".build-venv\Scripts\python.exe" -m pip install -r requirements-build.txt
if errorlevel 1 goto failed
".build-venv\Scripts\python.exe" tools\build_windows.py %*
if errorlevel 1 goto failed
echo Build succeeded. See dist\latest-windows.txt for the full output folder.
pause
exit /b 0

:failed
echo Build failed. Previous output folders are preserved.
pause
exit /b 1
