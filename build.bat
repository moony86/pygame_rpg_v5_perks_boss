@echo off
cd /d "%~dp0"

set BLUECUBE_DEV_TOOLS=0

set "BUILD_PYTHON=python"
if exist ".venv\Scripts\python.exe" set "BUILD_PYTHON=.venv\Scripts\python.exe"
"%BUILD_PYTHON%" -m nuitka ^
    --standalone ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico=assets\cube.ico ^
    --output-filename=BlueCube.exe ^
    --include-data-dir=assets=assets ^
    --include-data-dir=data=data ^
    --output-dir=dist_nuitka_demo ^
    --remove-output ^
    main.py

pause
