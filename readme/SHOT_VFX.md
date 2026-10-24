# Shot presentation and asset audit

Four new transparent PNG source assets, generated with the built-in image tool:
`assets/visuals/shot_charge.png`, `shot_trail.png`, `shot_sparks.png`, `shot_flame.png`.
Full prompts: `readme/shot-vfx-prompts.json`.

Fifteen independent `fx_` bindings in the visual library cover metal/magic/fire charge,
tails, fragments and hit overlays, plus hostile-magic tails/fragments/overlays.
Image, size, tint and opacity are editable; hit duration uses the existing `life` field.
Generated sources are single-frame assets with procedural travel/fade/flicker,
not authored animation sheets. Enemy cast body/telegraph geometry remains code-native.

## Runtime

- Player pistol: visual preparation in the latter half of the existing fire interval
  while firing, plus release flash at its registered muzzle. No hold-to-charge mechanic,
  initial delay, extra damage or fire-rate change. Normal bullets remain metallic;
  existing Surge uses magic presentation; existing explosive rounds use fire presentation.
- Ranged/hunter/elite/boss: charge follows actual windup/release, no fake attack loop.
- Player/drone/shuriken/enemy projectiles: bounded actual-path history (max 8 points,
  .12s); homing tails curve along the real trajectory. Hostile magic stays red/pink.
- Falling shots: the old vertical solid stroke is replaced by the tail asset.
- Successful direct, splash, shield, wall and enemy-to-player bullet hits use the
  same central VFX interface. Shield hits scatter energy without attaching flames.
- Flying fragments consume no gameplay RNG. Target overlays weakly reference their
  targets and stop when targets die; they never add burn/poison/slow damage or status.
- Fire overlay is cosmetic on explosive hits. Its .55s duration is not a burn debuff.
- Dedicated melee/blade effects are retained instead of adding duplicate shot effects.
- 96 simultaneous hit effects maximum; .12s trails; bounded prepared pose/fade/ribbon caches.
  New rounds clear rendering caches and pooled projectile initialization clears trails.

## Gaps closed in this pass

The asset-rendering early return previously bypassed legacy trails; all normal moving
projectile render paths now draw tails before their body. Hit VFX had only one generic
impact; styles now distinguish fragments and target overlays. Added missing standalone
charge, trail, fragment and flame artwork. This is a shot/VFX audit, not a claim that
all remaining UI/Hub artwork, sprite-sheet animation or release QA is complete.

Checks: `tools/check_shot_presentation.py` validates real fire hits without extra
damage, curve history, pool reset, shield behavior, expiry, caps, weak references,
asset validation and no gameplay RNG consumption. Pistol geometry and fire-rate
regressions remain covered by the original checks.
