@echo off
cd /d "%~dp0"
set "EDITOR_PYTHON="
if exist ".venv\Scripts\python.exe" set "EDITOR_PYTHON=%CD%\.venv\Scripts\python.exe"
if defined EDITOR_PYTHON goto run
if exist ".build-venv\Scripts\python.exe" set "EDITOR_PYTHON=%CD%\.build-venv\Scripts\python.exe"
if defined EDITOR_PYTHON goto run
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "EDITOR_PYTHON=%LocalAppData%\Programs\Python\Python312\python.exe"
if defined EDITOR_PYTHON goto run
python -c "import sys, pygame; assert sys.version_info[:2] == (3,12)" >nul 2>&1
if not errorlevel 1 set "EDITOR_PYTHON=python"
if defined EDITOR_PYTHON goto run
py -3.12 -c "import pygame" >nul 2>&1
if not errorlevel 1 goto launcher
echo Python 3.12 with pygame-ce was not found.
echo Install Python 3.12 and requirements.txt, or run build.bat to prepare .build-venv.
goto failed

:run
"%EDITOR_PYTHON%" -c "import sys, pygame; assert sys.version_info[:2] == (3,12)"
if errorlevel 1 goto failed
if /i "%~1"=="--check" exit /b 0
"%EDITOR_PYTHON%" tools\level_editor.py
if errorlevel 1 goto failed
exit /b 0

:launcher
if /i "%~1"=="--check" exit /b 0
py -3.12 tools\level_editor.py
if errorlevel 1 goto failed
exit /b 0

:failed
echo Editor could not start or exited with an error.
if /i not "%~1"=="--check" pause
exit /b 1
