@echo off
cd /d "%~dp0"

rem Frozen builds disable developer tools automatically; tests use source defaults.
set BLUECUBE_DEV_TOOLS=

if not exist ".build-venv\Scripts\python.exe" (
    call :create_env
    if errorlevel 1 goto failed
)
".build-venv\Scripts\python.exe" -m pip install -r requirements-build.txt
if errorlevel 1 goto failed
".build-venv\Scripts\python.exe" tools\build_windows.py %*
if errorlevel 1 goto failed
echo Build succeeded. See dist\latest-windows.txt for the full output folder.
pause
exit /b 0

:create_env
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" -m venv .build-venv
    if errorlevel 1 exit /b 1
    exit /b 0
)
where python >nul 2>nul
if not errorlevel 1 (
    python -c "import sys; assert sys.version_info[:2] == (3,12), 'Python 3.12 is required'"
    if errorlevel 1 exit /b 1
    python -m venv .build-venv
    if errorlevel 1 exit /b 1
    exit /b 0
)
where py >nul 2>nul
if not errorlevel 1 (
    py -3.12 -m venv .build-venv
    if errorlevel 1 exit /b 1
    exit /b 0
)
echo Python 3.12 was not found. Install Python 3.12, then run build.bat again.
exit /b 1

:failed
echo Build failed. Previous output folders are preserved.
pause
exit /b 1
