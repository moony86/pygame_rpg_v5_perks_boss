# Windows demo release status

Status: COMPLETE — source uploaded, Windows onedir build and archive verified.

Authorized scope: original class sounds, preserve visual/gameplay work and
user-authored hub/stage JSON, all regressions, Windows onedir build and frozen
verification, save results, push `codex/bluecube-demo-overhaul` to origin.

Class audio: 4 shoot + 4 impact WAV cues. Reproduce with
`tools/build_class_audio.py`; routing/gains in `assets/data/class_audio.json`.

Source commit: `a7c47b1f2245fbce728696e86f5c57c39e509f0e`.
Remote: `https://github.com/moony86/pygame_rpg_v5_perks_boss.git`.
Branch: `codex/bluecube-demo-overhaul` (no force push; main unchanged).

Windows build: `dist/windows-20261025-114250/BlueCube/BlueCube.exe`.
Share archive: `dist/BlueCube-Windows-20261025-114250.zip` (119344151 bytes).
ZIP SHA256: `81430154aef36e57abb4d562f19ddfe79482a2b0d106ccecf9c1c4947e7c9e0e`.

Validation: 28/28 isolated suites, including headless gameplay checks; frozen
EXE resource/game-loop smoke passed with class audio and all four skins.
All build-manifest file hashes matched, zero missing/corrupt files. The build
records a clean source tree at the source commit above. This report-only commit
does not change the compiled gameplay code.

Unzip the complete BlueCube folder, then run BlueCube.exe. Keep `_internal`.
No Python required for players. The build remains unsigned and is a development
demo for friends/testing, not a claim of production readiness or license clearance.
Known Vampire behavior issues remain documented in vampire-guide.md, unchanged.
Original older asset/music rights still require review before public release.

The 06:00 Asia/Riyadh fallback should now be disabled; no unfinished work remains
in this request. Do not repeat completed builds or pushes from a future follow-up.
