# Asset provenance — additions in Level Studio

## Sanctuary / hub additions (2026-10-24)

`assets/hub/sanctuary_v1.png`, `blacksmith_v1.png`, `healer_v1.png`,
`seer_v1.png`, and `tea_vendor_v1.png` were generated with built-in OpenAI
ImageGen under developer direction. Original PNGs, including transparency and
provenance metadata, are retained without offline image editing. Prompt record:
`readme/hub-generation-prompts.json`. Runtime paths/display sizes:
`assets/data/hub.json`. Portal art reuses the existing generated object binding.

Read `RIGHTS_AND_NOTICES.md` for ownership limitations, dependency attribution,
and the unresolved license review of older assets/music before public release.

- `assets/environment/cube_dungeon_atlas_v1.png`: new environment atlas generated
  using the built-in OpenAI ImageGen tool for this project. No commercial game
  texture pack or external third-party download was used for this addition.
  Full generation prompt and rendering notes: `readme/LEVEL_STUDIO.md`.
- Editor icons are Unicode characters; interface uses installed system fonts
  (Segoe UI / Tahoma), not bundled font files.

This records the new environment/editor assets only; it is not a licensing audit
of assets that were already present in the project.

## Object library additions

`assets/objects/`: new blue cube, portal, pistol, Ninja sword, green health potion
and dash crystal, generated using built-in ImageGen. The two atlas drafts are
retained for provenance; final standalone sprites avoid cross-cell clipping.
Generation prompts and runtime bindings are documented in `readme/OBJECT_LIBRARY.md`.

## Combat and card visual library

`assets/visuals/` and `assets/cards/art_v2/`: 37 new standalone PNG assets generated
using built-in ImageGen: eight enemy families, projectiles, XP, impact/ring/slash/
explosion VFX, a card frame and 21 card illustrations. Existing art is retained.
Variants share source art where documented but have independent visual bindings.
The existing `coin.png` animation is reused through the editable resource binding;
its original provenance is outside this additions-only record.
Full final generation prompts: `readme/visual-generation-prompts.json`.
Runtime/editor guide: `readme/VISUAL_LIBRARY.md`.

## Shot VFX additions

Four new transparent PNG sources in `assets/visuals/shot_*.png` generated using
built-in ImageGen: charge, magic trail, impact fragments and target flames.
Prompts: `readme/shot-vfx-prompts.json`. Runtime/editing notes: `readme/SHOT_VFX.md`.

## Warden trial, cube HUD and feedback audio

Follow-up assets `assets/visuals/boss_turret_v1.png` and `speed_wake_v1.png`
were generated with built-in ImageGen, preserving transparent originals.
Full prompts and integration notes: `readme/SANCTUARY_AND_PROGRESSION.md`.

`assets/visuals/boss_healing_eye_v1.png` and `hud_health_cell_v1.png`: generated
with built-in ImageGen, transparent originals retained. Full prompts:
`readme/boss-hud-generation-prompts.json`. The parry orb reuses the existing
`shot_charge.png` source through its own editable visual binding.

The 15 new feedback WAV cues (heal/boost/time-stop, boss tells, eye break/heal,
parry, player hurt and low health) are original procedural synthesis, not sampled
recordings or sounds taken from another game. Reproducible source:
`tools/build_feedback_audio.py`. Mix and runtime guide: `readme/BOSS_TRIAL_AUDIO_HUD.md`.
