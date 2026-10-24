# Demo overhaul — 2026-10-24

## 2026-10-25 — sanctuary authoring and route pressure

- Added Sanctuary Studio within Level Studio: drag actors/gate/spawn, rectangle and polygon invisible walls, precise coordinates, snap, undo/redo, walk preview, reachability validation, atomic saves and backups. Original hub placement/background preserved for developer authoring.
- Ordinary enemy difficulty now follows fixed route depth plus cleared combat rooms, with bounded contact damage, rather than staying at 1.0. No player-DPS matching or recolored enemy redesign.
- Boss arena is separated from transit routes; all combat rooms must be cleared by default, then a dedicated gate appears in the current cleared room and requires explicit confirmation. Former boss map location remains a reward-free passage.
- Warden approaches faster and attacks more often; phase transitions summon 5 then 6 stronger guards. Timed two-turret siege hazards and delayed radial follow-ups preserve visible warnings and escape sectors; boss HP was not increased.
- New transparent turret/speed-wake artwork is editable via the asset library. Tea now has an explicit on-screen T prompt. Added progression/editor/hazard regression checks and four-build bot diagnostics with honestly labeled fixtures.

## Sanctuary and Windows onedir follow-up

- New full sanctuary background and four transparent keeper sprites, with cached rendering, scene labels, perimeter colliders and role-based station placement.
- Contextual portrait-backed shop panels support mouse/number-key purchases and actual upgrade effects. Legacy replacement skills are explicitly marked; no balance removal hidden in the UI pass.
- Added five hub regression checks and native render captures; duplicate guidance hidden during dialogue.
- Windows build now uses pinned PyInstaller onedir in an isolated build environment. Dated outputs preserve previous builds, with full test gate, actual frozen-EXE resource smoke, player instructions, license material and SHA-256 manifest. Installer requires an explicit verified folder.
- Added factual AI-art disclosure and rights notices; existing music/asset licensing remains unresolved before a public release. No claim of automatic exclusive copyright or store readiness.

Branch: `codex/bluecube-demo-overhaul`. Base: `c44930c` (previous main). No history rewrite or force push.

## Gameplay and progression

- Fast-action roguelite direction, four starters: Gunslinger, Ninja, Engineer and Vampire. Temporary pistol-only weapon policy retains unique class mechanics.
- Ninja dash/sword finishers, bounded kill chains and directional timed boss-orb parry.
- Engineer shooter/blade/bomber companion presentation and progression; Vampire wound/Blood/Feast/bat/trail ecosystem.
- Stage routing, room bounds/colliders, starter reroll, perk presentation and loot collection feedback improvements.

## Warden encounter

- Three phases, readable windups, shared damage budgets and phase gates instead of inflated HP. Targetable healing eyes and a reflectable cyan orb.
- Two ascent intermissions: 3 then 4 guards, telegraphed spawn locations, out-of-reach boss, bounded duration, no XP/gold farming and a three-second landing opening.
- Guard/charge rejects ordinary damage. Airborne boss is excluded from target selection, ground-contact damage and projectile blocking. Ascent clears boss-owned shots.
- Final ascent pass leaves ordinary rooms and boss HP unchanged. Earlier validation: 15 boss tests, 23 general groups; three bot stage completions, boss times 57.07 / 47.38 / 41.65 seconds. Bot favors shooting and has no dash policy; not human balance certification.

## Visuals, audio and UI

- Asset-based dungeon floor/walls/obstacles, portals/player/weapons/potions/boost objects and editable bindings.
- Enemy-family animation/presentation, differentiated drones, visual cards, XP, charge/trails/impact/status VFX and time-stop feedback.
- Bounded presentation caches, projectile resource reuse and horde-oriented optimizations; no universal FPS guarantee.
- Main/settings/controls front end, persistent preferences, proportional graphical cube health, phase/objective HUD and reduced clutter.
- Distinct pickup/clock/warning/parry/hurt/low-health cues. New synthesized audio has reproducible source; original pre-existing assets have not received a comprehensive licensing audit.

## Editing and QA

- Local Level Studio GUI for stage layouts and object/visual bindings, with authored JSON and original assets in source control.
- Isolated optional private browser harness, not a supported web/mobile release.
- Regression suites for mechanics, authoring, assets, actors, presentation caches, menus/preferences, pickups and boss gates; separate full-run bot and benchmarks.

## Repository cleanup

- Moved `tools/check_*.py` and `tools/headless_checks.py` into `tests/`; same root depth, imports preserved. Historical reports may show old commands: use the identical basename under `tests/`.
- Added isolated `tests/run_all.py` and read-only `tools/audit_imports.py`.
- Updated three stale checks to match the existing catalog-backed card art, overlay-owned time-stop countdown and explicit legacy shield fallback. Full reorganized suite: 20/20 scripts passed, including the 23-group general harness. No game behavior was weakened to make old tests pass.
- Moved root reviews to `readme/audits/`, old Design Bible to `readme/design/`, scratch `123.txt` build note to `archive/notes/`.
- Untracked 96 old standalone distribution files from Git without deleting locally existing builds. Earlier committed outputs remain recoverable in history.
- Preserved pre-existing deletions of duplicate `files/` modules, obsolete `systems/ui.py` and Nuitka crash report. They remain recoverable at the base commit.
- Ignore virtual environments, local assistant metadata, snapshots, QA screenshots, generated reports, archives and build/installer outputs. Keep all source/assets needed for another machine.
- Import audit reached every non-package-marker runtime module in the six runtime packages. No runtime module was archived just because its name sounded old; active editor paths are retained.
- Portable play/editor launchers and refreshed build instructions. No EXE rebuild or store publication in this source checkpoint.

## Open design/release issues

- Healer shop still replaces Dash with Blast/Surge/Ghost, potentially conflicting with Ninja. Surge: five seconds, ×2 damage and ×1.45 fire-rate tuning. Not silently removed.
- No active Hyper fifth starter was found in inspected live source; HYBRID is shared-card metadata. Historical intent remains uncertain.
- Still require human runs for each build, native Windows frame-time checks, clean-machine packaging and asset-license review before public release.
# Window identity and menu pose

- Corrected the menu pistol to aim left, away from the hero.
- Replaced the obsolete v0.5 window title with Blue Cube — Demo.
- Set the native window icon and regenerated the multi-resolution EXE icon from existing blue hero art.

