@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" tools\level_editor.py
) else (
    py -3.12 tools\level_editor.py
)
if errorlevel 1 pause
