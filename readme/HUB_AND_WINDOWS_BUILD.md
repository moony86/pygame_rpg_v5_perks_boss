# Sanctuary and Windows onedir pass — 2026-10-24

## Design and interaction

The previous hub had a green debug grid, primitive NPC drawings and an unstyled shop list. The sanctuary is now a full background image with a single northern challenge gate, four readable keeper silhouettes on role-colored station pads, contextual interaction prompts and portrait-backed purchase panels.

Five new original ImageGen PNGs are stored in `assets/hub/`; prompts are recorded in `hub-generation-prompts.json`. Original metadata and transparency are preserved. `assets/data/hub.json` holds art paths, display dimensions, labels, role colors and basic perimeter colliders. NPCs keep their real game roles, purchases, dialogue and collision bodies; the portal's invisible interaction anchor represents the gate, not a duplicate character under it.

Press E near a keeper to open/close dialogue. Forge and healer offer click or number-key purchases. Every row shows price and actual shop effect; old skills explicitly say they replace Dash. No new build or balance changes were introduced. Ambient NPC bobbing reuses cached artwork; this is not a new multi-frame character animation sheet.

Visual QA: native Pygame render captures for the sanctuary and every keeper panel were inspected, then a second pass replaced misleading blade/double-barrel labels with pistol-appropriate names, clarified effects and removed duplicate guidance while dialogue is open. Captures live locally under `debug_screenshots/hub/`. A browser interaction attempt was interrupted by Chrome closing; it is not counted as a successful manual test. The dedicated automated tests validate contextual click purchases, unaffordable purchases, approach positions, transparency/caching and non-mutating rendering.

## Build workflow

`build.bat` creates/reuses `.build-venv`, installs the pinned Windows build requirements and runs `tools/build_windows.py`. Internet is needed on first install or when dependencies are not cached. Python 3.12 x64 must be installed on the build machine. No Python is needed on the player's machine.

The builder runs all regression suites in isolation, creates a new dated output using PyInstaller's explicit **onedir** mode, copies notices/licenses, then runs the produced EXE with an automated frozen-resource smoke check. Previous outputs are preserved. Missing dependencies, test failures, build failure or failed smoke checks return a failure exit code; a failed output should not be distributed.

```text
dist/windows-YYYYMMDD-HHMMSS/BlueCube/
  BlueCube.exe
  _internal/             Python/pygame DLLs, application modules and assets
  licenses/
  CREDITS.md
  RIGHTS_AND_NOTICES.md
  READ_ME_FIRST.txt
  smoke-test.json
  build-manifest.json
```

`dist/latest-windows.txt` points to the most recent successfully validated folder. Copy the entire BlueCube directory to another Windows machine. Do not copy just the EXE or mix support files from different builds. No onefile extraction or installer is required.

For code-only iteration an experienced developer can use `--skip-tests`; the manifest records that choice. Normal `build.bat` does not skip tests. Rebuild after source or asset changes. Generated executables and virtual environments are ignored by Git.

The frozen smoke is an offline automated check of menu, hub art, all card art, NPC panels, short combat frame execution and reset. It is not a full human playthrough, audio listening check, clean-machine test, code-signing certificate or native FPS certification. Windows SmartScreen may warn about an unsigned executable; do not tell testers it is signed or bypass security protections.

## Validation record

The isolated Python 3.12 build completed at `dist/windows-20261024-171414/BlueCube/`.
All 21 regression scripts passed, including five focused sanctuary checks.
The produced EXE passed its frozen-resource smoke from inside the distribution
folder. The earlier global-environment build and obsolete Nuitka output were
subsequently removed at the developer's request; the validated output above was
preserved. A failed intermediate build ran out of space; generated QA staging
copies and failed output/work directories were also cleaned, not game source.

## Rights and public-release limits

`RIGHTS_AND_NOTICES.md` is copied alongside the EXE, with installed dependency license texts and CPython's license where available. The menu discloses AI-assisted art and points to included notices. Existing-asset licensing is still a public-release gate; developer output rights are not a guarantee of exclusive copyright over every AI-generated pixel or ownership of pre-existing music.
