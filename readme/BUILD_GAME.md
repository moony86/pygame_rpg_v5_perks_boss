# Blue Cube build guide

Start with Python 3.12 and the root README's `.venv` setup. Install Nuitka
separately into that build environment (not needed to run the game); a compatible
Windows C compiler is also required. Run `tests/run_all.py` before packaging.

This project uses Nuitka to create the playable Windows build that `setup.iss`
later packages into an installer.

## 1. Build the game folder

Open PowerShell in this folder:

```powershell
cd pygame_rpg_v5_perks_boss
```

Run the standalone Nuitka build:

```powershell
.\build.bat
```

The game exe will be created here:

```text
dist_nuitka_demo\main.dist\BlueCube.exe
```

## 2. Quick test

Run:

```powershell
.\dist_nuitka_demo\main.dist\BlueCube.exe
```

Opening the game is only a smoke check. Verify full runs, native frame times,
and the standalone folder on another machine before installer packaging.
This branch has not rebuilt or certified a new EXE. Preserve any old output
you need before building: the build command can replace its output directory.

## 3. Build the installer later

`setup.iss` already points to:

```text
.\dist_nuitka_demo\main.dist\BlueCube.exe
.\dist_nuitka_demo\main.dist\*
```

So after rebuilding the game, open `setup.iss` with Inno Setup and compile it.
The installer output goes to:

```text
installer_output\BlueCube_v0.5_Setup.exe
```

## Notes

- Source and assets are tracked; generated EXEs, DLLs and installers are not.
- Installer version metadata remains 0.5 until a deliberate release version update.
- No store publication is performed here.

- Rebuild with Nuitka after changing Python code or assets.
- Packaged/frozen builds default dev tools off automatically. The release build
  command still sets `BLUECUBE_DEV_TOOLS=0` before invoking Nuitka as an explicit
  safety signal. Normal source runs with `python main.py` leave the variable
  unset, which keeps developer tools enabled for local development.
- Keep the `assets` folder included, because the player, gun, bullets, sounds,
  and music are loaded from there.
- If Nuitka reports an SCons/cache lock, close any running build process and try
  again after a minute.
