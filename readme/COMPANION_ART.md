# Companion presentation

Generated with the built-in image generation tool, transparent PNGs in `assets/visuals/`.
Editable through Level Studio's visual object library (restart the editor server after this update).

Bindings: `companion_drone` (sentry gun), `companion_blade` (spinning blades),
`companion_bomber` (orange bomb carrier), `companion_bat`, `companion_blood`
(reserve indicator and dropped blood). Existing abilities, collision, timers and damage are unchanged.
The bat has a subtle procedural wing squash, not an authored frame-by-frame animation.
Bomb cooldown arcs and attack telegraphs remain precise procedural indicators.

## Distinct drones — 2026-10-24

| Editable object | Source PNG | Default draw box |
| --- | --- | --- |
| companion_drone | assets/visuals/companion_sentry_v2.png | 48 x 44 |
| companion_blade | assets/cards/art_v2/blade_drone.png | 44 x 44 |
| companion_bomber | assets/cards/art_v2/bomber_drone.png | 50 x 44 |

The blade and bomber reuse the existing transparent card illustrations, without
changing card bindings or card files. This intentionally matches what the player
selected. The sentry is a new transparent PNG generated using built-in imagegen;
the complete prompt is in `readme/drone-generation-prompts.json`.
Original shared drone PNG is preserved for rollback/custom authored content.

The sentry mirrors toward its own last fired target, independently for upgraded
multiple sentries. Before the first shot it follows player aim. This is facing,
not a new full-angle turret or new aiming/target-selection mechanic.
Blades use their real spin angle and retained ghost trail. Gun firing and blade
hits briefly brighten the sprite. Both hovering bodies gently bob and bank.
Bomber remains visible, dimmed, during its actual cooldown with a progress arc.
Animations are procedural poses of single PNGs, not authored sprite sheets.

No damage, collision radii, firing cadence, machine counts or perk values changed.
Bomber still flies into targets and explodes: it does NOT drop a separate bomb.
A carried-bomb silhouette is visual only in this pass.

Level Studio exposes each binding separately: art, dimensions, tint, opacity,
frame count/grid and FPS. Restart an already-running editor to load new bindings,
then refresh its tab. Existing saved custom overrides are preserved; choose the
new PNG manually if an older customized catalog overrides the default binding.

`systems/companion_presentation.py` shares quantized 5-degree poses and faded
variants with a maximum of 512 entries / 8 MiB, invalidated on catalog revision.
No per-frame blade transform/copy is needed once a pose is warm. Pose quantization
does not alter actual blade orbit, collision or spin simulation.

Verification: `tools/check_companion_presentation.py` (7 tests),
`tools/check_render_performance.py` (9 tests), `tools/headless_checks.py` (23 groups).
Private browser fixture `?scene=drones` grants existing level-1 machine upgrades
and two real-AI enemies for visual QA only; it is not normal room balance.
Actual browser movement/fire confirmed, with bomber flight and cooldown captured
in `debug_screenshots/drones-attack-v2.png` and `drones-live-v2.png`.
The static 1x / enlarged comparison is `debug_screenshots/companion-presentation.png`.
This smoke test is not a full-run or native performance certification.

## Generation prompts

- Drone: Single game sprite, transparent background. BlueCube dark dungeon pixel-art companion: tiny cyan-steel hovering blade drone, circular luminous cyan core and four silver cutting fins, top-down three-quarter view, chunky crisp 32-bit pixel art readable at 36px. Centered isolated, no text, no border, no ground, no shadow, no card. One object only.
- Bat: Single game sprite, transparent background. BlueCube dark dungeon vampire companion: small crimson and violet bat with two spread angular wings, glowing pink eyes, ruby blood gem chest, top-down three-quarter view, chunky crisp 32-bit pixel art readable at 36px. Centered isolated, no text, no border, no ground, no shadow, no card. One bat only.
- Blood: Single game sprite transparent background. BlueCube dark dungeon collectible: floating faceted ruby blood droplet with dark burgundy metal claw setting and small pink specular highlight, chunky crisp 32-bit pixel art readable at 20px, isolated centered, no text, no border, no ground, no shadow. One object only.

## Facing

New hero/enemy art is authored facing left. Mirror when facing right.
Hero presentation follows horizontal aim, retaining the previous direction near vertical aim;
strafing does not turn the body away from the pistol. Pistol muzzle calculations are unchanged.
