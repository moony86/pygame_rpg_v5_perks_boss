# Blue Cube build guide

This project uses Nuitka to create the playable Windows build that `setup.iss`
later packages into an installer.

## 1. Build the game folder

Open PowerShell in this folder:

```powershell
cd C:\Users\abdulkrem\Desktop\pygame_rpg_v5_perks_boss
```

Run the standalone Nuitka build:

```powershell
python -m nuitka --standalone --windows-console-mode=disable --include-data-dir=assets=assets --include-data-dir=data=data --output-dir=dist_nuitka_demo main.py
```

The game exe will be created here:

```text
dist_nuitka_demo\main.dist\main.exe
```

## 2. Quick test

Run:

```powershell
.\dist_nuitka_demo\main.dist\main.exe
```

If the game opens, the build is ready for installer packaging.

## 3. Build the installer later

`setup.iss` already points to:

```text
.\dist_nuitka_demo\main.dist\main.exe
.\dist_nuitka_demo\main.dist\*
```

So after rebuilding the game, open `setup.iss` with Inno Setup and compile it.
The installer output goes to:

```text
installer_output\BlueCube_v5_Setup.exe
```

## Notes

- Rebuild with Nuitka after changing Python code or assets.
- Keep the `assets` folder included, because the player, gun, bullets, sounds,
  and music are loaded from there.
- If Nuitka reports an SCons/cache lock, close any running build process and try
  again after a minute.
