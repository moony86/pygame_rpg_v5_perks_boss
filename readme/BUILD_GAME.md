# Build BlueCube for Windows (onedir)

Install **Python 3.12 x64** on the build machine, then double-click `build.bat`
or run it from the repository root:

```powershell
.\build.bat
```

The script creates an isolated `.build-venv`, installs the pinned dependencies
from `requirements-build.txt`, runs the full regression suite, builds with
PyInstaller 6.21.0 in explicit **onedir** mode and runs the resulting EXE's
offline frozen-resource check. First dependency installation requires internet.
Nuitka and a C compiler are not required for this workflow.

Each build is a new dated directory; previous builds are preserved:

```text
dist/windows-YYYYMMDD-HHMMSS/BlueCube/BlueCube.exe
dist/windows-YYYYMMDD-HHMMSS/BlueCube/_internal/
```

`dist/latest-windows.txt` points to the latest successful output. Copy the
**entire BlueCube folder** to the player's Windows machine. No Python install,
onefile extraction, ZIP or installer is needed for the player. Never copy just
the EXE or mix its `_internal` folder with another build.

The output includes player instructions, CREDITS, rights/dependency notices,
installed license material, an automated smoke report and a SHA-256 build
manifest. Failure of tests/build/smoke returns a nonzero status. A failed dated
folder may remain for diagnostics and should not be distributed.

After source or asset edits, run `build.bat` again. Expert local iteration can
call `.build-venv/Scripts/python.exe tools/build_windows.py --skip-tests`, but
that fact is recorded in the manifest; normal builds do not skip tests.

An optional Inno Setup script remains available: `setup.iss` now requires an
explicit `BuildFolder` define pointing to a verified onedir folder. It no
longer silently packages the stale Nuitka output. No installer is built here.

Automated checks do not replace human playtests, clean-machine verification,
native frame-time measurements or license review. This is an unsigned test
EXE, not a code-signed public release. Read
[HUB_AND_WINDOWS_BUILD.md](HUB_AND_WINDOWS_BUILD.md) and the root
`RIGHTS_AND_NOTICES.md` before distribution.
