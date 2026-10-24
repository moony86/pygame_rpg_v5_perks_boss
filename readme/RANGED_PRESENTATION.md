# Ranged caster presentation pass

Visual-only procedural animation of existing editable enemy PNGs, not an authored
frame-by-frame sprite sheet. Applies to RANGED, RANGED_THREE, RANGED_FIVE and RANGED_RAIN.

- Gentle hover/lean during locomotion.
- Windup compression and a growing violet casting point driven by actual windup progress.
- Facing follows the locked attack direction during windup/release.
- Release recoil starts when `_finish_windup` emits the attack event, followed by recovery.
- Hit recoil takes visual precedence without cancelling the underlying attack.
- A 280ms fading/shrinking death echo persists independently after the enemy is removed.
- Existing attack payloads, trajectories, warning lines, damage, cooldowns, collision and rewards unchanged.
- Presentation timers advance only in Enemy.update, so pause/time-stop don't advance them through draw calls.

Checks: `tools/check_ranged_presentation.py` (4), `tools/check_visual_library.py` (7),
`tools/headless_checks.py` (23 groups). Private browser shared-loop smoke test includes
movement, shooting and dash; it does not establish desktop performance or full-run balance.
